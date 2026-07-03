# NetGuardian Video Script

Target length: 5 minutes or less.

## 0:00 - 0:30 Problem

"Security teams are drowning in logs. The hard part is not just seeing malware. It is understanding who owns the device, what business systems it can access, what the risk is, and how to respond safely."

## 0:30 - 1:10 Product

"NetGuardian is an Enterprise Security Operating System powered by AI agents. The center is not the LLM. The center is the Enterprise Digital Twin: users, devices, relationships, business context, telemetry, threat intelligence, incidents, approvals, and audit logs."

## 1:10 - 1:50 Architecture

Show the Mermaid diagram or README architecture.

"Telemetry flows through a Python Event Dispatcher into Enterprise State. The Incident Engine creates incidents deterministically. Then an ADK-style coordinator runs Investigation, Response, and Verification agents. Dangerous actions require human approval and execute only through an MCP-style boundary."

## 1:50 - 3:40 Live Demo

1. Open dashboard.
2. Click Reset Demo.
3. Click Run Alice Malware Events.
4. Show Alice owns Employee-01 and Employee-01 has access to `FILE-01` and the Payroll Database.
5. Show risk score and evidence.
6. Run Investigation Agent.
7. Run Response Agent.
8. Ask "Why is this not just a false positive?"
9. Point out evidence, reasoning, recommendation, trade-off, confidence, and required approval.
10. Approve isolation.
11. Execute isolation via MCP.
12. Run Verification Agent.
13. Show containment passed, `FILE-01` safe, and Payroll Database safe.

## 3:40 - 4:30 Course Concepts

"This project demonstrates multi-agent design, analyst follow-up reasoning, an MCP-style tool boundary, human-in-the-loop security, local evaluation, deployability with Docker Compose, and safe agentic engineering. The current MVP uses deterministic ADK-style agents for reproducibility, can use local Ollama or Gemini for analyst-facing reasoning, and includes a clear path to wrap these roles as live ADK agents."

## 4:30 - 5:00 Close

"NetGuardian shows how agents can support business security operations without becoming an unsafe black box. The platform creates incidents from trusted state, agents explain and recommend, humans approve, MCP executes, and verification closes the loop."
