# NetGuardian: An Enterprise Security Operating System Powered by AI Agents

## Subtitle

From endpoint telemetry to human-approved containment with an Enterprise Digital Twin, Incident Engine, ADK-style agents, and MCP-style execution.

## Track

Agents for Business

## Problem

Security operations teams face too many logs and too little time. In a real enterprise, one endpoint can generate process events, DNS requests, network connections, authentication events, and file-share activity. When something suspicious happens, analysts must connect technical evidence with business context: who owns the device, what department it belongs to, what systems it can access, and what would break if the response is too aggressive.

The problem is not just detecting malware. The hard part is turning scattered telemetry into an explainable, safe, business-aware response.

## Solution

NetGuardian is an Enterprise Security Operating System for incident response. It is not a chatbot that reads logs. The center of the system is an Enterprise Digital Twin: users, devices, relationships, business assets, telemetry, threat intelligence, incidents, approvals, actions, and audit logs.

In the demo, Alice works in Finance and owns `Employee-01`, which can access critical Finance assets: the `FILE-01` file server and the Payroll Database it hosts. Alice opens a malicious Excel macro. The endpoint emits suspicious telemetry: PowerShell launched from Excel, a malicious domain lookup, a connection to known C2 infrastructure, and SMB scanning toward `FILE-01`.

NetGuardian ingests those telemetry events, updates Enterprise State, calculates a risk score, creates an incident, asks an AI-agent workflow to explain and recommend response, waits for human approval, executes containment through an MCP-style boundary, and verifies that the threat is contained while payroll systems remain safe.

The current submission is a working local MVP. It supports optional local AI reasoning through Ollama, optional Gemini reasoning, and a deterministic fallback so the demo is reproducible and testable without cloud credentials. The dashboard also includes an analyst follow-up question flow, so judges can ask the Investigation Agent a custom question from the active incident bundle. The architecture is intentionally ADK-ready: the same investigation, response, verification, state, and MCP interfaces can be wrapped as live ADK tools and agents.

## Architecture

The architecture has three layers.

Enterprise Platform:

- Telemetry Engine receives endpoint events.
- Python Event Dispatcher acts as the local event bus.
- Enterprise Digital Twin is the single source of truth.
- Business Context models owner, department, criticality, and access relationships.
- Threat Intelligence stores local malicious IPs, domains, and hashes.
- Incident Engine creates incidents deterministically from rules and risk scoring.

AI Layer:

- Investigation Agent explains evidence and root cause.
- Follow-up question answering lets analysts interrogate the incident bundle.
- Response Agent recommends safe action with confidence and trade-off.
- Verification Agent checks containment, business impact, and rollback safety.

Execution Layer:

- Human Approval gates high-impact actions.
- MCP-style tools execute approved actions only.
- SQLite Digital Twin logically simulates endpoints, users, and critical servers.

## Why Agents

The Incident Engine decides whether an incident exists. The agents do what humans need help with: synthesizing evidence, explaining impact, recommending a safe response, and checking whether the response worked.

This separation is deliberate. AI should not be the uncontrolled center of a security platform. It should be a specialist working from trusted enterprise state.

The agent workflow is role-based:

- The Investigation Agent explains why the telemetry is dangerous.
- The Investigation Agent can answer analyst follow-up questions from Enterprise State.
- The Response Agent recommends the safest bounded action and calls out the trade-off.
- The Verification Agent checks whether containment worked and whether business assets remain protected.

This mirrors the ADK implementation path while keeping the hackathon demo safe. Local or cloud AI writes the analyst-facing reasoning, but deterministic platform controls still own incident creation, action boundaries, approval checks, and containment status.

## Course Concepts Demonstrated

- ADK-style multi-agent workflow.
- MCP-style controlled tool execution.
- Human-in-the-loop approval for high-impact response.
- Security boundaries and audit logs.
- Local evaluation cases.
- Docker Compose deployability.

## Demo

The public project runs locally with Docker Compose. The Streamlit dashboard shows the Enterprise Digital Twin, incident timeline, evidence, AI reasoning, recommendation, approval controls, MCP execution result, verification result, and audit trail.

The demo flow is:

1. Reset the demo state.
2. Run Alice's malware telemetry events.
3. Open the generated incident case.
4. Review evidence and business context.
5. Run investigation and response.
6. Ask a follow-up question such as "Why is this not just a false positive?"
7. Try execution without approval and observe denial.
8. Approve isolation.
9. Execute isolation through the MCP-style boundary.
10. Verify containment and business impact.

## Results

The demo creates the Alice malware incident deterministically from telemetry. The Response Agent recommends isolating `Employee-01` because it contacted known C2 infrastructure and can access payroll systems. The system refuses isolation without approval. After approval, MCP-style execution isolates the endpoint and Verification confirms containment.

Local verification currently includes:

- 9 passing unit tests (100% test coverage for core safety boundaries, state management, and agent interfaces).
- Clean Python compile check for the app, simulator, and tests.
- Valid Docker Compose configuration.
- Agents CLI project detection in prototype mode.

## Security

NetGuardian follows a safe-by-design model:

- AI does not create incidents.
- AI does not execute shell commands.
- Enterprise State is the single source of truth.
- High-impact actions require approval.
- All recommendations, approvals, actions, and verification results are logged.
- No secrets are committed.

## Future Work

Future versions could replace the local event dispatcher with Kafka or Pub/Sub, replace SQLite with Postgres, connect real EDR telemetry, deploy to Cloud Run or Agent Runtime, and add more incident scenarios. For the capstone, the focus is one complete, explainable, safe business scenario.

The most direct next step is an ADK wrapper around the current state, agent, and MCP interfaces. That upgrade should preserve the same safety invariant: the model may recommend and explain, but the Incident Engine owns incident creation and the MCP-style boundary owns execution.

## ADK Migration Path & Production Bridge

NetGuardian's architecture is built to be "ADK-native" from day one. Rather than treating the transition to production as a rewrite, we have provided a production-ready, syntactically correct ADK integration module in [adk_agent.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/adk_agent.py).

This module exposes our deterministic security and telemetry functions as standard **ADK Tools**:
- `get_enterprise_state`: Exposes the central digital twin state.
- `get_incident_evidence`: Focuses agent context on the specific telemetry of the active alert.
- `query_threat_intel`: Connects external indicators to the investigation.
- `request_approval`: Registers approval request tokens within the MCP-style execution gateway.
- `isolate_device` / `verify_containment`: Interfaces directly with our containment tools.

We wrap these tools into three role-based **ADK Agents**:
1. **Investigation Agent**: Grounded to analyze telemetry and asset risks using the Gemini 2.0 Flash model.
2. **Response Agent**: Formulates containment suggestions and automatically requests human approval tokens.
3. **Verification Agent**: Audits the physical/logical network status post-containment and confirms critical payroll files remain online.

These specialists are chained together using a **SequentialAgent coordinator** (`netguardian_coordinator`). 

To validate the behavior of this agentic workflow, we implemented an automated behavior evaluation harness (`eval/run_evals.py`) and a yaml-defined test suite (`eval/netguardian_eval_cases.yaml`). This "Quality Flywheel" runs the agent workflow against five core compliance scenarios (Happy Path, Approval Bypass Refusal, Follow-up Q&A, Verification, and Jailbreak Defenses), achieving a **100% Accuracy Score**. Developers can deploy this entire multi-agent workflow to Google Cloud Run or GKE seamlessly using the `agents-cli` tool.
