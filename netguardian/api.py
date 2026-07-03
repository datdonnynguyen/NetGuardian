from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .ai_provider import agent_mode
from .agents import NetGuardianAgents
from .database import init_db, rows
from .enterprise_state import EnterpriseState
from .mcp_tools import NetGuardianMCP
from .seed import reset_demo

try:
    from fastapi import FastAPI, HTTPException
except ModuleNotFoundError:  # Allows core tests without FastAPI installed.
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore


class TelemetryEvent(BaseModel):
    device_id: str
    event_type: str
    value: str
    severity: int = 1
    details: str = ""


class ApprovalRequest(BaseModel):
    action: str = "isolate_device"
    target_id: str = "employee-01"
    approver: str = "Security Admin"


class ExecuteRequest(BaseModel):
    approval_id: int
    token: str
    target_id: str = "employee-01"


class QuestionRequest(BaseModel):
    question: str


def create_app() -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed. Install requirements.txt or use Docker Compose.")

    init_db()
    app = FastAPI(title="NetGuardian API", version="0.1.0")
    state = EnterpriseState()
    agents = NetGuardianAgents()
    mcp = NetGuardianMCP()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "netguardian-api"}

    @app.get("/agent-mode")
    def api_agent_mode() -> dict:
        return agent_mode()

    @app.post("/demo/reset")
    def api_reset_demo() -> dict:
        return reset_demo()

    @app.post("/demo/run-events")
    def api_run_demo_events() -> dict:
        return state.ingest_demo_events()

    @app.post("/events")
    def api_ingest_event(event: TelemetryEvent) -> dict:
        return state.ingest_event(event.model_dump())

    @app.get("/state")
    def api_state() -> dict:
        return state.get_state()

    @app.get("/incidents")
    def api_incidents() -> list[dict]:
        return rows("SELECT * FROM incidents ORDER BY id DESC")

    @app.get("/incidents/{incident_id}")
    def api_incident(incident_id: int) -> dict:
        bundle = state.get_incident(incident_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="incident_not_found")
        return bundle

    @app.post("/incidents/{incident_id}/investigate")
    def api_investigate(incident_id: int) -> dict:
        result = agents.investigate(incident_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    @app.post("/incidents/{incident_id}/recommend")
    def api_recommend(incident_id: int) -> dict:
        result = agents.recommend_response(incident_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    @app.post("/incidents/{incident_id}/ask")
    def api_ask(incident_id: int, request: QuestionRequest) -> dict:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="question_required")
        result = agents.answer_question(incident_id, request.question)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    @app.post("/incidents/{incident_id}/approve")
    def api_approve(incident_id: int, request: ApprovalRequest) -> dict:
        return mcp.request_approval(incident_id, request.action, request.target_id, request.approver)

    @app.post("/incidents/{incident_id}/reject")
    def api_reject(incident_id: int, request: ApprovalRequest) -> dict:
        return mcp.reject_action(incident_id, request.action, request.target_id, request.approver)

    @app.post("/incidents/{incident_id}/execute/isolate")
    def api_execute_isolate(incident_id: int, request: ExecuteRequest) -> dict:
        return mcp.isolate_device(incident_id, request.target_id, request.approval_id, request.token)

    @app.post("/incidents/{incident_id}/verify")
    def api_verify(incident_id: int) -> dict:
        return mcp.verify_containment(incident_id)

    @app.get("/incidents/{incident_id}/report")
    def api_report(incident_id: int) -> dict:
        bundle = state.get_incident(incident_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="incident_not_found")
        
        incident = bundle["incident"]
        device = bundle["device"]
        owner = bundle["owner"]
        evidence = bundle["evidence"]
        critical_assets = bundle["critical_assets"]
        approvals = bundle["approvals"]
        actions = bundle["actions"]
        telemetry = bundle["telemetry_events"]
        
        md = []
        md.append(f"# NetGuardian SOC Incident Audit Report")
        md.append(f"**Incident ID:** NG-{incident['id']:04d}")
        md.append(f"**Title:** {incident['title']}")
        md.append(f"**Current Status:** {incident['status'].upper()}")
        md.append(f"**Risk Score:** {incident['risk_score']}/100")
        md.append(f"**Created By:** {incident['created_by']}")
        md.append(f"**Timestamp:** {incident['created_at']}")
        md.append("")
        
        md.append(f"## 1. Asset & Owner Context")
        md.append(f"- **Affected Endpoint:** {device['hostname']} (Network Status: {device['network_status'].upper()})")
        md.append(f"- **Owner:** {owner['name']} (Department: {device['department']}, Role: {owner['role']})")
        md.append(f"- **Asset Criticality:** {device['criticality'].upper()}")
        md.append("")
        md.append("### Related Business Assets & Risk Impact")
        for asset in critical_assets:
            md.append(f"- **{asset['name']}** ({asset['asset_type'].replace('_', ' ').title()}) - Criticality: {asset['criticality'].upper()} - Department: {asset['department']}")
        md.append("")
        
        md.append(f"## 2. Telemetry Evidence Timeline")
        for event in telemetry:
            md.append(f"- `[{event['created_at']}]` **{event['event_type'].replace('_', ' ').upper()}**: {event['value']} (Severity: {event['severity']}/10)")
            if event['details']:
                md.append(f"  *Details:* {event['details']}")
        md.append("")
        
        md.append(f"## 3. Threat Analysis & Evidence Scoring")
        for item in evidence:
            md.append(f"- **{item['evidence_type'].replace('_', ' ').title()}**: {item['summary']} (Risk weight: +{item['weight']})")
        md.append("")
        
        md.append(f"## 4. SOC Human-In-The-Loop Approval & Actions")
        if not approvals:
            md.append("*No approvals requested or recorded for this incident.*")
        else:
            for app in approvals:
                md.append(f"- **Action:** `{app['action']}` on target `{app['target_id']}`")
                md.append(f"  *Approver:* {app['approver']} | *Status:* {app['status'].upper()}")
                md.append(f"  *Token:* `{app['token']}`")
                md.append(f"  *Timestamp:* {app['created_at']}")
        md.append("")
        
        md.append("### MCP Execution History")
        if not actions:
            md.append("*No MCP actions executed for this incident.*")
        else:
            for act in actions:
                md.append(f"- **Action:** `{act['action']}` on target `{act['target_id']}`")
                md.append(f"  *Result Status:* {act['status'].upper()}")
                md.append(f"  *Outcome Details:* {act['result']}")
                md.append(f"  *Timestamp:* {act['created_at']}")
        md.append("")
        
        md.append(f"## 5. Closure & Verification Summary")
        md.append(f"**Containment Status:** {'CONTAINED' if device['network_status'] == 'isolated' else 'ACTIVE'}")
        md.append(f"**Business Impact Assessment:** {incident['business_impact']}")
        md.append("")
        md.append("---")
        md.append("*Report generated automatically by NetGuardian Security Operating System.*")
        
        report_text = "\n".join(md)
        return {"incident_id": incident_id, "report_markdown": report_text}

    @app.get("/threat-intel")
    def api_threat_intel(indicator: str | None = None) -> list[dict]:
        return mcp.query_threat_intel(indicator)

    return app


app = create_app() if FastAPI is not None else None
