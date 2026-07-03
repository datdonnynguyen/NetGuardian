from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_URL = os.getenv("NETGUARDIAN_API_URL", "http://localhost:8000")
API_TIMEOUT_SECONDS = float(os.getenv("NETGUARDIAN_DASHBOARD_API_TIMEOUT_SECONDS", "20"))
AGENT_TIMEOUT_SECONDS = float(os.getenv("NETGUARDIAN_DASHBOARD_AGENT_TIMEOUT_SECONDS", "120"))


def api(method: str, path: str, **kwargs):
    timeout = kwargs.pop("timeout", API_TIMEOUT_SECONDS)
    response = requests.request(method, f"{API_URL}{path}", timeout=timeout, **kwargs)
    response.raise_for_status()
    return response.json()


def run_agent_request(label: str, path: str) -> dict[str, Any] | None:
    try:
        with st.spinner(f"{label} is running with the local model. First run can take up to two minutes."):
            return api("POST", path, timeout=AGENT_TIMEOUT_SECONDS)
    except requests.Timeout:
        st.error(
            f"{label} timed out while waiting for the local AI model. "
            "Try again once Ollama has finished loading the model, or increase NETGUARDIAN_DASHBOARD_AGENT_TIMEOUT_SECONDS."
        )
    except requests.RequestException as exc:
        st.error(f"{label} could not reach the NetGuardian API: {exc}")
    return None


def ask_agent_request(incident_id: int, question: str) -> dict[str, Any] | None:
    try:
        with st.spinner("Investigation Agent is answering with the current incident bundle."):
            return api("POST", f"/incidents/{incident_id}/ask", json={"question": question}, timeout=AGENT_TIMEOUT_SECONDS)
    except requests.Timeout:
        st.error(
            "Investigation Agent timed out while answering. "
            "Try again once the local model is warm, or increase NETGUARDIAN_DASHBOARD_AGENT_TIMEOUT_SECONDS."
        )
    except requests.RequestException as exc:
        st.error(f"Investigation Agent could not reach the NetGuardian API: {exc}")
    return None


def refresh_state() -> dict[str, Any]:
    state = api("GET", "/state")
    st.session_state["state"] = state
    return state


def card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="ng-card">
          <div class="ng-card-label">{label}</div>
          <div class="ng-card-value">{value}</div>
          <div class="ng-card-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def table_rows(items: list[tuple[str, str]]) -> None:
    st.dataframe(
        [{"Field": label, "Value": value} for label, value in items],
        use_container_width=True,
        hide_index=True,
    )


def render_agent_mode(result: dict[str, Any]) -> None:
    mode = result.get("mode", "deterministic")
    model = result.get("model", "deterministic-fallback")
    if mode == "live_gemini":
        st.success(f"Agent Mode: Live Gemini ({model})")
    elif mode == "local_ollama":
        st.success(f"Agent Mode: Local Ollama ({model})")
    else:
        reason = result.get("fallback_reason")
        suffix = f" | Fallback: {reason}" if reason else ""
        st.info(f"Agent Mode: Deterministic fallback ({model}){suffix}")


def render_digital_twin_graph(owner_name: str, device_hostname: str, network_status: str, risk_score: int) -> None:
    is_isolated = network_status.lower() == "isolated"
    device_class = "twin-success" if is_isolated else ("twin-danger" if risk_score > 70 else "")
    device_badge = "🔴 RISK HIGH" if risk_score > 70 and not is_isolated else ("🟢 CONTAINED" if is_isolated else "🟢 SECURE")
    network_text = "ISOLATED" if is_isolated else "CONNECTED"
    
    st.markdown(
        f"""
        <div class="twin-container">
          <div class="twin-node">
            <div class="twin-node-title">Owner</div>
            <div class="twin-node-value">👤 {owner_name}</div>
            <div class="twin-node-desc">Finance Dept</div>
          </div>
          <div class="twin-arrow">➔</div>
          <div class="twin-node {device_class}">
            <div class="twin-node-title">Endpoint Device</div>
            <div class="twin-node-value">💻 {device_hostname}</div>
            <div class="twin-node-desc">{network_text} | {device_badge}</div>
          </div>
          <div class="twin-arrow">➔</div>
          <div class="twin-node">
            <div class="twin-node-title">Access Route</div>
            <div class="twin-node-value">📁 FILE-01</div>
            <div class="twin-node-desc">Finance File Server</div>
          </div>
          <div class="twin-arrow">➔</div>
          <div class="twin-node">
            <div class="twin-node-title">Critical Data Asset</div>
            <div class="twin-node-value">🗄️ Payroll Database</div>
            <div class="twin-node-desc">Secure & Protected</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    normalized = status.lower()
    if normalized in {"active", "failed", "denied"}:
        tone = "danger"
    elif normalized in {"responding", "approved"}:
        tone = "warning"
    elif normalized in {"contained", "succeeded", "passed"}:
        tone = "success"
    else:
        tone = "neutral"
    return f'<span class="ng-badge ng-{tone}">{status.upper()}</span>'


def ensure_case_state(incident_id: int) -> dict[str, Any]:
    key = f"case_{incident_id}"
    if key not in st.session_state:
        st.session_state[key] = {}
    return st.session_state[key]


def render_timeline(events: list[dict], evidence: list[dict]) -> None:
    evidence_by_event = {
        item["source_event_id"]: item for item in evidence if item.get("source_event_id") is not None
    }
    for event in events:
        item = evidence_by_event.get(event["id"])
        weight = f"+{item['weight']} risk" if item else "context"
        st.markdown(
            f"""
            <div class="timeline-item">
              <div class="timeline-top">
                <strong>{event['event_type'].replace('_', ' ').title()}</strong>
                <span>{weight}</span>
              </div>
              <div class="timeline-value">{event['value']}</div>
              <div class="timeline-details">{event['details']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.set_page_config(page_title="NetGuardian SOC", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
      .ng-header {border-bottom: 1px solid #263241; padding-bottom: 0.8rem; margin-bottom: 1rem;}
      .ng-eyebrow {font-size: 0.78rem; text-transform: uppercase; color: #6b7280; letter-spacing: 0.08em;}
      .ng-title {font-size: 2rem; font-weight: 750; line-height: 1.1;}
      .ng-subtitle {color: #6b7280; margin-top: 0.25rem;}
      .ng-card {border: 1px solid #263241; border-radius: 8px; padding: 0.9rem; background: #0f1722; color: #f8fafc; min-height: 108px;}
      .ng-card-label {font-size: 0.78rem; text-transform: uppercase; color: #cbd5e1;}
      .ng-card-value {font-size: 1.35rem; font-weight: 750; margin-top: 0.25rem;}
      .ng-card-caption {font-size: 0.85rem; color: #dbeafe; margin-top: 0.35rem;}
      .ng-badge {border-radius: 999px; padding: 0.18rem 0.5rem; font-size: 0.75rem; font-weight: 700;}
      .ng-danger {background: #fee2e2; color: #991b1b;}
      .ng-warning {background: #fef3c7; color: #92400e;}
      .ng-success {background: #dcfce7; color: #166534;}
      .ng-neutral {background: #e5e7eb; color: #374151;}
      .case-strip {border: 1px solid #263241; border-radius: 8px; padding: 0.85rem; background: #111827; color: #f8fafc; margin-bottom: 0.65rem;}
      .case-title {font-weight: 750; font-size: 1.05rem; color: #f8fafc;}
      .case-meta {color: #dbeafe; font-size: 0.88rem; margin-top: 0.25rem;}
      .section-title {font-weight: 750; margin-top: 0.4rem; margin-bottom: 0.5rem;}
      .timeline-item {border-left: 3px solid #38bdf8; padding: 0.2rem 0 0.8rem 0.85rem; margin-left: 0.2rem;}
      .timeline-top {display: flex; justify-content: space-between; gap: 1rem; color: #dbeafe;}
      .timeline-top span {font-size: 0.8rem; color: #93c5fd;}
      .timeline-value {font-family: monospace; margin-top: 0.2rem;}
      .timeline-details {color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem;}
      .demo-step {border-left: 3px solid #334155; padding: 0.2rem 0 0.6rem 0.65rem; color: #475569; font-size: 0.9rem;}
      .demo-step strong {color: #0f172a;}
      .ng-note {border: 1px solid #334155; border-radius: 8px; background: #0b1220; padding: 0.85rem; color: #cbd5e1; margin: 0.5rem 0 0.8rem;}
      .ng-note strong {color: #f8fafc;}
      .twin-container {
        display: flex;
        align-items: center;
        justify-content: space-around;
        background: #0f1722;
        border: 1px solid #263241;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        gap: 0.5rem;
        flex-wrap: wrap;
      }
      .twin-node {
        flex: 1;
        text-align: center;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #334155;
        background: #111827;
        color: #f8fafc;
        min-width: 150px;
        box-sizing: border-box;
      }
      .twin-node-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 700;
        margin-bottom: 0.25rem;
      }
      .twin-node-value {
        font-size: 0.95rem;
        font-weight: 750;
      }
      .twin-node-desc {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.2rem;
      }
      .twin-arrow {
        font-size: 1.5rem;
        color: #3b82f6;
        user-select: none;
        font-weight: bold;
      }
      .twin-danger {
        border-color: #ef4444;
        background: #270f0f;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.45);
      }
      .twin-success {
        border-color: #10b981;
        background: #062f21;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.45);
      }
      .adk-info-panel {
        border: 1px solid #2563eb;
        border-radius: 8px;
        background: #0b1329;
        padding: 0.85rem;
        color: #cbd5e1;
        margin-top: 1rem;
      }
      .adk-info-panel strong {
        color: #38bdf8;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ng-header">
      <div class="ng-eyebrow">NetGuardian SOC Console</div>
      <div class="ng-title">Incident Response Workspace</div>
      <div class="ng-subtitle">Enterprise Digital Twin, deterministic incident creation, AI-assisted response, human approval, and MCP-controlled execution.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Demo Controls")
    st.markdown(
        """
        <div class="demo-step"><strong>1.</strong> Reset the Enterprise Digital Twin.</div>
        <div class="demo-step"><strong>2.</strong> Run Alice malware telemetry.</div>
        <div class="demo-step"><strong>3.</strong> Investigate, approve, execute, verify.</div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Reset Demo", use_container_width=True):
        api("POST", "/demo/reset")
        st.session_state.clear()
        refresh_state()
        st.success("Demo reset")
        st.rerun()
    if st.button("Run Alice Malware Events", use_container_width=True):
        api("POST", "/demo/run-events")
        refresh_state()
        st.success("Telemetry events ingested")
        st.rerun()
    st.divider()

state = st.session_state.get("state") or refresh_state()
mode_info = api("GET", "/agent-mode")
incidents = state["incidents"]
devices = state["devices"]
assets = state["business_assets"]
telemetry = state["telemetry_events"]
audit_logs = state["audit_logs"]

with st.sidebar:
    st.header("Incident Cases")
    if incidents:
        case_options = {
            f"NG-{incident['id']:04d} | {incident['status'].upper()} | Risk {incident['risk_score']}": incident["id"]
            for incident in incidents
        }
        selected_label = st.radio("Select a case", list(case_options.keys()), label_visibility="collapsed")
        selected_incident_id = case_options[selected_label]
    else:
        selected_incident_id = None
        st.info("Run the demo events to create a case.")

overview_cols = st.columns(4)
with overview_cols[0]:
    card("Open Cases", str(len([item for item in incidents if item["status"] != "closed"])), "Incident Engine generated cases")
with overview_cols[1]:
    endpoint_count = len(devices)
    card("Endpoints", str(endpoint_count), "Only endpoint devices are counted here")
with overview_cols[2]:
    critical_count = len([asset for asset in assets if asset["criticality"] == "critical"])
    card("Critical Assets", str(critical_count), "FILE-01 and Payroll Database")
with overview_cols[3]:
    card("Agent Mode", str(mode_info["active"]).replace("_", " ").title(), str(mode_info["model"]))

st.divider()

if selected_incident_id is None:
    st.info("Use the sidebar to reset the demo and run Alice malware events. A selectable incident case will appear here.")
    st.stop()

bundle = api("GET", f"/incidents/{selected_incident_id}")
incident = bundle["incident"]
device = bundle["device"]
owner = bundle["owner"]
critical_assets = bundle["critical_assets"]
relationships = bundle["relationships"]
evidence = bundle["evidence"]
events = bundle["telemetry_events"]
case_state = ensure_case_state(selected_incident_id)

st.markdown(
    f"""
    <div class="case-strip">
      <div class="case-title">NG-{incident['id']:04d}: {incident['title']} {status_badge(incident['status'])}</div>
      <div class="case-meta">Created by {incident['created_by']} | Risk score {incident['risk_score']} | Affected endpoint {device['hostname']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

summary_cols = st.columns([1.1, 1, 1])
with summary_cols[0]:
    st.markdown('<div class="section-title">Case Summary</div>', unsafe_allow_html=True)
    st.write(incident["business_impact"])
    st.progress(min(int(incident["risk_score"]), 100) / 100, text=f"Risk Score: {incident['risk_score']}")
with summary_cols[1]:
    st.markdown('<div class="section-title">Affected Endpoint</div>', unsafe_allow_html=True)
    st.dataframe(
        [
            {
                "Endpoint": device["hostname"],
                "Owner": owner["name"],
                "Department": device["department"],
                "Criticality": device["criticality"],
                "Network": device["network_status"],
            }
        ],
        use_container_width=True,
        hide_index=True,
    )
with summary_cols[2]:
    st.markdown('<div class="section-title">Related Critical Assets</div>', unsafe_allow_html=True)
    st.dataframe(
        [
            {
                "Asset": asset["name"],
                "Type": asset["asset_type"],
                "Department": asset["department"],
                "Criticality": asset["criticality"],
            }
            for asset in critical_assets
        ],
        use_container_width=True,
        hide_index=True,
    )

tab_overview, tab_evidence, tab_ai, tab_execution, tab_audit = st.tabs(
    ["Business Context", "Evidence Timeline", "AI Investigation", "Approval and MCP", "Verification and Audit"]
)

with tab_overview:
    st.markdown('<div class="section-title">Digital Twin Access & Risk Propagation Flow</div>', unsafe_allow_html=True)
    render_digital_twin_graph(owner["name"], device["hostname"], device["network_status"], incident["risk_score"])
    
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="section-title">Enterprise Digital Twin Relationships</div>', unsafe_allow_html=True)
        st.dataframe(relationships, use_container_width=True, hide_index=True)
    with right:
        st.markdown('<div class="section-title">Threat Intelligence</div>', unsafe_allow_html=True)
        st.dataframe(state["threat_intel"], use_container_width=True, hide_index=True)

with tab_evidence:
    left, right = st.columns([1.25, 1])
    with left:
        st.markdown('<div class="section-title">Telemetry Timeline</div>', unsafe_allow_html=True)
        render_timeline(events, evidence)
    with right:
        st.markdown('<div class="section-title">Risk Evidence</div>', unsafe_allow_html=True)
        st.dataframe(evidence, use_container_width=True, hide_index=True)

with tab_ai:
    action_cols = st.columns(2)
    if action_cols[0].button("Run Investigation Agent", use_container_width=True):
        result = run_agent_request("Investigation Agent", f"/incidents/{selected_incident_id}/investigate")
        if result:
            case_state["investigation"] = result
    if action_cols[1].button("Run Response Agent", use_container_width=True):
        result = run_agent_request("Response Agent", f"/incidents/{selected_incident_id}/recommend")
        if result:
            case_state["recommendation"] = result
    investigation = case_state.get("investigation")
    recommendation = case_state.get("recommendation")
    if investigation:
        st.markdown('<div class="section-title">Investigation</div>', unsafe_allow_html=True)
        render_agent_mode(investigation)
        st.write(investigation["summary"])
        st.write(investigation["reasoning"])
        st.caption(investigation["business_context"])
        st.metric("Investigation Confidence", f"{investigation['confidence']}%")
        st.dataframe([{"Evidence": item} for item in investigation["evidence"]], use_container_width=True, hide_index=True)
    if recommendation:
        st.markdown('<div class="section-title">Recommendation</div>', unsafe_allow_html=True)
        render_agent_mode(recommendation)
        st.write(recommendation["recommendation"])
        rec_cols = st.columns(3)
        rec_cols[0].metric("Action", recommendation["action"])
        rec_cols[1].metric("Target", recommendation["target_id"])
        rec_cols[2].metric("Confidence", f"{recommendation['confidence']}%")
        st.warning(recommendation["tradeoff"])
        st.caption("Human approval is required before MCP execution.")
    st.markdown('<div class="section-title">Ask Investigation Agent</div>', unsafe_allow_html=True)
    follow_up_question = st.text_input(
        "Ask a follow-up question",
        value=case_state.get("follow_up_question", "Why is this not just a false positive?"),
    )
    if st.button("Ask Agent", use_container_width=True):
        case_state["follow_up_question"] = follow_up_question
        if follow_up_question.strip():
            result = ask_agent_request(selected_incident_id, follow_up_question)
            if result:
                case_state["follow_up_answer"] = result
        else:
            st.warning("Enter a question for the Investigation Agent.")
    if "follow_up_answer" in case_state:
        answer = case_state["follow_up_answer"]
        render_agent_mode(answer)
        st.write(answer["answer"])
        st.metric("Answer Confidence", f"{answer['confidence']}%")
        st.dataframe([{"Evidence": item} for item in answer["evidence"]], use_container_width=True, hide_index=True)

with tab_execution:
    st.markdown('<div class="section-title">Human Approval Gate</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ng-note">
          <strong>Safety proof:</strong> MCP execution rejects isolation unless the approval id, action, target, and token all match.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Test Unapproved Isolation", use_container_width=True):
        case_state["denied_execution"] = api(
            "POST",
            f"/incidents/{selected_incident_id}/execute/isolate",
            json={"approval_id": 999, "token": "invalid-demo-token", "target_id": "employee-01"},
        )
        refresh_state()
        st.rerun()
    if "denied_execution" in case_state:
        denied = case_state["denied_execution"]
        st.error(f"Unapproved MCP execution: {denied['status'].upper()} ({denied.get('reason', 'no reason')})")

    approval_cols = st.columns(2)
    if approval_cols[0].button("Approve Isolation", use_container_width=True):
        case_state["approval"] = api(
            "POST",
            f"/incidents/{selected_incident_id}/approve",
            json={"action": "isolate_device", "target_id": "employee-01", "approver": "Security Admin"},
        )
        refresh_state()
        st.rerun()
    if approval_cols[1].button("Reject Isolation", use_container_width=True):
        case_state["approval"] = api(
            "POST",
            f"/incidents/{selected_incident_id}/reject",
            json={"action": "isolate_device", "target_id": "employee-01", "approver": "Security Admin"},
        )
        refresh_state()
        st.rerun()
    if "approval" in case_state:
        approval = case_state["approval"]
        st.markdown('<div class="section-title">Approval Decision</div>', unsafe_allow_html=True)
        table_rows(
            [
                ("Status", approval["status"].upper()),
                ("Approval ID", str(approval["approval_id"])),
                ("Token", f"{approval['token'][:6]}...{approval['token'][-4:]}"),
            ]
        )
        if approval["status"] == "approved" and st.button("Execute Isolation via MCP", use_container_width=True):
            case_state["execution"] = api(
                "POST",
                f"/incidents/{selected_incident_id}/execute/isolate",
                json={
                    "approval_id": approval["approval_id"],
                    "token": approval["token"],
                    "target_id": "employee-01",
                },
            )
            refresh_state()
            st.rerun()
    if "execution" in case_state:
        st.markdown('<div class="section-title">MCP Execution Result</div>', unsafe_allow_html=True)
        execution = case_state["execution"]
        table_rows(
            [
                ("Status", execution["status"].upper()),
                ("Device", execution.get("device_id", "employee-01")),
                ("Network", execution.get("network_status", "unchanged")),
            ]
        )
    st.markdown('<div class="section-title">Approvals</div>', unsafe_allow_html=True)
    st.dataframe(bundle["approvals"], use_container_width=True, hide_index=True)
    st.markdown('<div class="section-title">Actions</div>', unsafe_allow_html=True)
    st.dataframe(bundle["actions"], use_container_width=True, hide_index=True)

with tab_audit:
    if st.button("Run Verification Agent", use_container_width=True):
        case_state["verification"] = api("POST", f"/incidents/{selected_incident_id}/verify")
        refresh_state()
        st.rerun()
    if "verification" in case_state:
        verification = case_state["verification"]
        st.markdown('<div class="section-title">Verification Result</div>', unsafe_allow_html=True)
        render_agent_mode(verification)
        v_cols = st.columns(3)
        v_cols[0].metric("Containment", verification["containment"])
        v_cols[1].metric("Business Impact", "Protected")
        v_cols[2].metric("Rollback", "Not Required" if verification["containment"] == "passed" else "Review")
        st.write(verification["business_impact"])
        st.caption(verification["rollback_validation"])
        
        st.divider()
        try:
            report_data = api("GET", f"/incidents/{selected_incident_id}/report")
            report_md = report_data.get("report_markdown", "")
            st.download_button(
                label="📥 Download SOC Incident Audit Report",
                data=report_md,
                file_name=f"netguardian_incident_NG-{selected_incident_id:04d}_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        except Exception as exc:
            st.error(f"Could not generate audit report: {exc}")
            
    st.markdown('<div class="section-title">Audit Trail</div>', unsafe_allow_html=True)
    st.dataframe(audit_logs, use_container_width=True, hide_index=True)
