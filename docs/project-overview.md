# NetGuardian Project Overview

## One-line Summary

NetGuardian is an Enterprise Security Operating System that helps security teams detect, investigate, approve, execute, and verify incident response actions through an Enterprise Digital Twin and AI-assisted SOC workflow.

## Product Summary

NetGuardian is not a chatbot that reads logs. It is an incident-centric SOC platform where the system owns the source of truth and AI agents act as security specialists.

The center of the platform is the Enterprise Digital Twin:

- Users.
- Endpoint devices.
- Critical business assets.
- Relationships between users, endpoints, and assets.
- Telemetry events.
- Threat intelligence.
- Incidents.
- Recommendations.
- Human approvals.
- MCP-style actions.
- Audit logs.

The AI layer reads this trusted state to explain what happened, recommend safe response options, and verify whether containment worked.

## Demo Scenario

Alice Nguyen works in Finance and owns `Employee-01`. That endpoint can access critical Finance assets:

- `FILE-01`, a critical Finance file server.
- `Payroll Database`, hosted by `FILE-01`.

Alice opens a malicious Excel macro. The endpoint emits telemetry:

- Excel spawns PowerShell.
- The endpoint resolves a malicious domain.
- The endpoint connects to known C2 infrastructure.
- The endpoint performs SMB discovery toward `FILE-01`.

The Incident Engine calculates risk from telemetry, threat intelligence, and business context. It creates a high-risk incident. The AI agents then explain the evidence, recommend isolating `Employee-01`, require human approval, execute the approved action through the MCP-style boundary, and verify that `FILE-01` and the Payroll Database remain safe.

## Architecture

```text
Endpoint Simulator
  -> Telemetry Event
  -> Event Dispatcher
  -> Telemetry Engine
  -> Enterprise Digital Twin
  -> Incident Engine
  -> Incident Case
  -> ADK-style Coordinator
  -> Investigation Agent
  -> Response Agent
  -> Human Approval
  -> MCP-style Execution
  -> Verification Agent
  -> Audit Trail
```

## Enterprise Digital Twin

Enterprise State is the single source of truth. Agents do not inspect Docker directly and do not create incidents directly.

Example relationship model:

```text
Alice Nguyen
  owns
Employee-01
  has_access_to
FILE-01
  hosts
Payroll Database
```

This relationship graph lets NetGuardian reason about business impact instead of treating every log line as isolated technical data.

## Incident Engine

The Incident Engine creates incidents deterministically. AI does not decide whether an incident exists.

Risk scoring for the demo includes:

- Suspicious PowerShell from Excel macro: +40.
- Known C2 IP from local threat intelligence: +30.
- SMB scan toward Finance file server: +20.
- Finance endpoint business context: +10.
- Access to payroll-related assets: +10.

Risk is capped at 100. When risk crosses the threshold, the Incident Engine creates a selectable SOC case.

## AI Agents

### Investigation Agent

Explains why the incident is dangerous using:

- Telemetry evidence.
- Threat intelligence.
- Endpoint ownership.
- Department context.
- Relationships to critical business assets.

### Response Agent

Recommends the safest response action. For the demo, it recommends isolating `Employee-01`.

The response output includes:

- Evidence.
- Reasoning.
- Recommendation.
- Trade-off.
- Confidence.
- Required approval.

### Verification Agent

Checks containment and business impact after execution:

- Endpoint isolation status.
- Whether the approved MCP action succeeded.
- Whether `FILE-01` and the Payroll Database remain protected.
- Whether rollback is needed.

## MCP-style Execution Boundary

The execution layer enforces human approval before high-impact actions.

Allowed demo actions:

- `isolate_device`.
- `block_ip`.
- `verify_containment`.

If approval is missing or invalid, execution is denied and recorded in the audit log.

## Dashboard

The dashboard is organized as an incident-centric SOC workflow:

- Selectable incident cases.
- Incident Detail view.
- Case summary.
- Affected endpoint.
- Related critical assets.
- Business context.
- Evidence timeline.
- AI investigation and recommendation.
- Approval and MCP execution.
- Verification and audit trail.

`Employee-01` is shown as the affected endpoint. `FILE-01` and the Payroll Database are shown as critical business assets, not regular endpoint devices.

## Technology Stack

| Component | Technology | Role |
| --- | --- | --- |
| Backend | FastAPI | Central API |
| State | SQLite | Enterprise Digital Twin |
| UI | Streamlit | SOC dashboard |
| Eventing | Python dispatcher | In-process event bus |
| Incident Logic | Python rules | Deterministic risk scoring |
| AI Layer | ADK-style agents | Investigation, response, verification |
| Execution | MCP-style tools | Safe approved action boundary |
| Demo Runtime | Docker Compose | Reproducible local demo |

## Hackathon Fit

NetGuardian demonstrates:

- Multi-agent system design.
- MCP-style controlled execution.
- Human-in-the-loop security.
- Enterprise security workflow.
- Evaluation and deterministic tests.
- Docker Compose deployability.

The chosen Kaggle track is `Agents for Business`.
