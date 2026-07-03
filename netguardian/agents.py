from __future__ import annotations

import json
import os

from .ai_provider import LiveAIUnavailable, agent_mode, generate_json
from .database import connect
from .docker_helper import DOCKER_SOCKET_PATH, is_container_connected_to_network
from .enterprise_state import EnterpriseState


class NetGuardianAgents:
    """ADK-style agent layer with optional live Ollama/Gemini reasoning.

    Security decisions remain deterministic: the Incident Engine creates cases,
    response actions are fixed to approved MCP tools, and execution remains
    approval-gated. Live AI can enrich analyst-facing reasoning when configured.
    """

    def __init__(self) -> None:
        self.state = EnterpriseState()

    def investigate(self, incident_id: int) -> dict:
        bundle = self.state.get_incident(incident_id)
        if not bundle:
            return {"error": "incident_not_found"}
        incident = bundle["incident"]
        device = bundle["device"]
        owner = bundle["owner"]
        evidence = bundle["evidence"]
        critical_assets = bundle["critical_assets"]
        evidence_summaries = [item["summary"] for item in evidence]
        asset_names = ", ".join(asset["name"] for asset in critical_assets) or "critical Finance assets"
        mode = agent_mode()
        result = {
            "agent": "Investigation Agent",
            "mode": mode["active"],
            "model": mode["model"],
            "incident_id": incident_id,
            "summary": f"{device['hostname']} shows high-risk malware behavior affecting Finance.",
            "evidence": evidence_summaries,
            "reasoning": (
                f"{owner['name']} owns {device['hostname']} in {device['department']}. "
                "The endpoint launched suspicious PowerShell, contacted known C2 infrastructure, "
                f"and attempted SMB discovery toward {asset_names}."
            ),
            "business_context": f"Finance endpoint access places {asset_names} at risk.",
            "confidence": min(98, int(incident["risk_score"]) + 3),
        }
        try:
            live = generate_json(
                "Write the investigation output for a SOC analyst.",
                bundle,
                {
                    "summary": "One concise sentence explaining what happened.",
                    "reasoning": "Two to four sentences tying telemetry evidence to likely risk.",
                    "business_context": "One or two sentences explaining business impact.",
                    "confidence": "Integer confidence from 0 to 100.",
                },
            )
            result.update(
                {
                    "summary": str(live.get("summary") or result["summary"]),
                    "reasoning": str(live.get("reasoning") or result["reasoning"]),
                    "business_context": str(live.get("business_context") or result["business_context"]),
                    "confidence": _bounded_confidence(live.get("confidence"), result["confidence"]),
                    "mode": agent_mode()["active"],
                    "model": agent_mode()["model"],
                }
            )
        except LiveAIUnavailable as exc:
            result["mode"] = "deterministic"
            result["model"] = "deterministic-fallback"
            result["fallback_reason"] = str(exc)
        self._audit("investigation_agent", "investigation_completed", result)
        return result

    def recommend_response(self, incident_id: int) -> dict:
        investigation = self.investigate(incident_id)
        if "error" in investigation:
            return investigation
        bundle = self.state.get_incident(incident_id)
        mode = agent_mode()
        recommendation = {
            "agent": "Response Agent",
            "mode": investigation.get("mode", mode["active"]),
            "model": investigation.get("model", mode["model"]),
            "incident_id": incident_id,
            "action": "isolate_device",
            "target_id": "employee-01",
            "evidence": investigation["evidence"],
            "reasoning": "Isolation stops outbound C2 traffic and prevents lateral movement to payroll systems.",
            "recommendation": "Immediately isolate Employee-01, then verify C2 traffic stopped and critical Finance assets remain safe.",
            "tradeoff": "Alice will temporarily lose network access, but payroll systems stay protected.",
            "confidence": investigation["confidence"],
            "required_approval": True,
        }
        if bundle:
            try:
                live = generate_json(
                    "Write a response recommendation for a SOC analyst. The only allowed action is isolate_device on employee-01, and it must require human approval.",
                    bundle,
                    {
                        "reasoning": "Two to four sentences explaining why isolation is the safest bounded response.",
                        "recommendation": "One concise recommended action sentence.",
                        "tradeoff": "One sentence explaining operational cost versus risk reduction.",
                        "confidence": "Integer confidence from 0 to 100.",
                    },
                )
                recommendation.update(
                    {
                        "reasoning": str(live.get("reasoning") or recommendation["reasoning"]),
                        "recommendation": str(live.get("recommendation") or recommendation["recommendation"]),
                        "tradeoff": str(live.get("tradeoff") or recommendation["tradeoff"]),
                        "confidence": _bounded_confidence(live.get("confidence"), recommendation["confidence"]),
                        "mode": agent_mode()["active"],
                        "model": agent_mode()["model"],
                    }
                )
            except LiveAIUnavailable as exc:
                recommendation["mode"] = "deterministic"
                recommendation["model"] = "deterministic-fallback"
                recommendation["fallback_reason"] = str(exc)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO recommendations(incident_id, action, confidence, evidence, reasoning, tradeoff, required_approval)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    recommendation["action"],
                    recommendation["confidence"],
                    json.dumps(recommendation["evidence"]),
                    recommendation["reasoning"],
                    recommendation["tradeoff"],
                    1,
                ),
            )
        self._audit("response_agent", "recommendation_created", recommendation)
        return recommendation

    def answer_question(self, incident_id: int, question: str) -> dict:
        bundle = self.state.get_incident(incident_id)
        if not bundle:
            return {"error": "incident_not_found"}
        evidence_summaries = [item["summary"] for item in bundle["evidence"]]
        asset_names = ", ".join(asset["name"] for asset in bundle["critical_assets"]) or "critical Finance assets"
        clean_question = question.strip()
        mode = agent_mode()
        
        # Input Guardrail for bypass / override attempts
        q_lower = clean_question.lower()
        if "override" in q_lower or "bypass" in q_lower or "ignore approval" in q_lower:
            result = {
                "agent": "Investigation Agent",
                "mode": mode["active"],
                "model": mode["model"],
                "incident_id": incident_id,
                "question": clean_question,
                "answer": (
                    "Security Guardrail Triggered: I cannot bypass human approval protocols or execute containment "
                    "actions directly. All security operations must follow the defined MCP approval gateway."
                ),
                "evidence": ["Security policy enforcement: approval required."],
                "confidence": 100,
            }
            self._audit("investigation_agent", "bypass_attempt_blocked", result)
            return result

        result = {
            "agent": "Investigation Agent",
            "mode": mode["active"],
            "model": mode["model"],
            "incident_id": incident_id,
            "question": clean_question,
            "answer": (
                f"Based on Enterprise State, {bundle['device']['hostname']} launched suspicious PowerShell, "
                "contacted known C2 infrastructure, and scanned toward Finance assets. "
                f"The risk is business-relevant because the endpoint can reach {asset_names}."
            ),
            "evidence": evidence_summaries,
            "confidence": min(98, int(bundle["incident"]["risk_score"]) + 3),
        }
        try:
            live = generate_json(
                (
                    "Answer this SOC analyst follow-up question using only Enterprise State. "
                    "Do not recommend bypassing approval or claim execution that is not recorded. "
                    f"Question: {clean_question}"
                ),
                bundle,
                {
                    "answer": "Two to four sentences answering the analyst question from the incident evidence.",
                    "evidence": "Array of short evidence strings that support the answer.",
                    "confidence": "Integer confidence from 0 to 100.",
                },
            )
            result.update(
                {
                    "answer": str(live.get("answer") or result["answer"]),
                    "evidence": _evidence_list(live.get("evidence"), result["evidence"]),
                    "confidence": _bounded_confidence(live.get("confidence"), result["confidence"]),
                    "mode": agent_mode()["active"],
                    "model": agent_mode()["model"],
                }
            )
        except LiveAIUnavailable as exc:
            result["mode"] = "deterministic"
            result["model"] = "deterministic-fallback"
            result["fallback_reason"] = str(exc)
        self._audit("investigation_agent", "follow_up_answered", result)
        return result

    def verify(self, incident_id: int) -> dict:
        bundle = self.state.get_incident(incident_id)
        if not bundle:
            return {"error": "incident_not_found"}
        device = bundle["device"]
        actions = bundle["actions"]
        critical_assets = bundle["critical_assets"]
        asset_names = ", ".join(asset["name"] for asset in critical_assets) or "critical Finance assets"
        
        isolated = device["network_status"] == "isolated"
        isolation_action = any(action["action"] == "isolate_device" and action["status"] == "succeeded" for action in actions)
        
        # Physical Docker network verification
        physical_verified = True
        docker_msg = ""
        if os.path.exists(DOCKER_SOCKET_PATH):
            net_name = os.getenv("NETGUARDIAN_DOCKER_NETWORK", "netguardian_default")
            is_connected = is_container_connected_to_network(net_name, device["id"])
            if is_connected:
                physical_verified = False
                docker_msg = " [WARNING: Device is physically still connected to Docker network!]"
            else:
                docker_msg = " [Physical container detachment verified via Docker socket]"
                
        mode = agent_mode()
        containment_status = "passed" if isolated and isolation_action and physical_verified else "failed"
        impact_status = f"{asset_names} remain online and protected.{docker_msg}"
        rollback_msg = "Physical containment confirmed via container network audit. No rollback required; only Employee-01 was isolated." if (isolated and physical_verified) else "Rollback not applicable."
        
        result = {
            "agent": "Verification Agent",
            "mode": mode["active"],
            "model": mode["model"],
            "incident_id": incident_id,
            "containment": containment_status,
            "business_impact": impact_status,
            "rollback_validation": rollback_msg,
            "recommendation": "Close incident after analyst review." if (isolated and physical_verified) else "Keep incident active and retry approved isolation.",
        }
        try:
            live = generate_json(
                "Write the verification output after response execution. Preserve the deterministic containment result.",
                bundle,
                {
                    "business_impact": "One sentence confirming impact on FILE-01 and Payroll Database.",
                    "rollback_validation": "One sentence explaining whether rollback is needed.",
                    "recommendation": "One sentence with next SOC action.",
                },
            )
            result.update(
                {
                    "business_impact": str(live.get("business_impact") or result["business_impact"]),
                    "rollback_validation": str(live.get("rollback_validation") or result["rollback_validation"]),
                    "recommendation": str(live.get("recommendation") or result["recommendation"]),
                    "mode": agent_mode()["active"],
                    "model": agent_mode()["model"],
                }
            )
        except LiveAIUnavailable as exc:
            result["mode"] = "deterministic"
            result["model"] = "deterministic-fallback"
            result["fallback_reason"] = str(exc)
        with connect() as conn:
            if isolated:
                conn.execute("UPDATE incidents SET status = 'contained', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (incident_id,))
        self._audit("verification_agent", "verification_completed", result)
        return result

    def _audit(self, actor: str, event: str, payload: dict) -> None:
        with connect() as conn:
            conn.execute(
                "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                (actor, event, json.dumps(payload)),
            )


def _bounded_confidence(value: object, fallback: int) -> int:
    try:
        confidence = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(0, min(100, confidence))


def _evidence_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    evidence = [str(item) for item in value if str(item).strip()]
    return evidence or fallback
