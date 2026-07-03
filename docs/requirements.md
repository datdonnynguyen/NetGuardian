# NetGuardian Requirements

## Product Goal

Build an Enterprise Security Operating System that demonstrates how AI agents can help a security team understand, approve, execute, and verify incident response actions.

## MVP Scenario

Alice in Finance opens a malicious Excel macro on `Employee-01`. The endpoint emits suspicious telemetry. NetGuardian creates a high-risk incident, explains the evidence, recommends isolating the endpoint, waits for approval, executes through MCP-style tools, and verifies that C2 traffic stopped while `FILE-01` and the Payroll Database remain safe.

## Functional Requirements

- Maintain an Enterprise Digital Twin with users, devices, relationships, business assets, telemetry, threat intel, incidents, approvals, actions, and audit logs.
- Ingest endpoint telemetry as events.
- Use an in-process Event Dispatcher for v1.
- Create incidents deterministically through an Incident Engine.
- Use local Threat Intelligence for known malicious IPs/domains/hashes.
- Provide ADK-style multi-agent outputs for investigation, response, and verification.
- Require human approval before high-impact actions.
- Provide a dashboard for incident review, approval, execution, and verification.
- Provide Docker Compose for a reproducible public demo.

## Non-Goals

- No Kafka/RabbitMQ for v1.
- No Kubernetes for v1.
- No live cloud deployment in the critical path.
- No multiple incident scenarios before the main malware isolation scenario is complete.
