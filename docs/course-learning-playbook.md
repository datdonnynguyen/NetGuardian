# Course Learning Playbook for NetGuardian

This document captures the 5-day AI Agents learning material and the user's completed/related labs so future sessions can apply the same techniques while building NetGuardian.

## Source Materials

Local knowledge PDFs:

- `knowledge/day 1/The New SDLC With Vibe Coding_Day_1.pdf`
- `knowledge/day2/Agent Tools & Interoperability_Day_2.pdf`
- `knowledge/day3/Vibe Coding Agent Security and Evaluation_Day_3 (1).pdf`
- `knowledge/day4/day4.pdf`
- `knowledge/day5/Day_5_v3 (1).pdf`

User-provided codelabs:

- Day 1:
  - Codelab 1: Getting started with Antigravity 2.0 and IDE
    - https://codelabs.developers.google.com/getting-started-google-antigravity#0
  - Codelab 2: Build a web app in AI Studio and deploy to Cloud Run
    - https://codelabs.developers.google.com/deploy-from-aistudio-to-run?hl=en#0
- Day 2:
  - Codelab 1: Getting started with Antigravity CLI
    - https://codelabs.developers.google.com/antigravity-cli-hands-on#0
  - Codelab 2: Google Developer Knowledge MCP server
    - https://codelabs.developers.google.com/developer-knowledge-mcp-antigravity
- Day 3:
  - Codelab 1: Antigravity Skills
    - https://codelabs.developers.google.com/getting-started-with-antigravity-skills?hl=en#4
  - Codelab 2: Build agents with Agents CLI and ADK
    - https://codelabs.developers.google.com/agents-cli-adk-lifecycle
- Day 4:
  - Codelab 1: Expense-approval agent with human-in-the-loop and local evaluations
    - https://codelabs.developers.google.com/vibecode-ambient-expense-agent
  - Codelab 2: Secure agentic coding, threat scans, safety guards, security testing
    - https://codelabs.developers.google.com/secure-agentic-coding
- Day 5:
  - Deploy agent to Google Cloud
    - https://codelabs.developers.google.com/enterprise-cloud-scale-deploying-the-expense-agent-to-agent-runtime-on-google-cloud
  - Build frontend web app connected to cloud agent
    - https://codelabs.developers.google.com/vibecode-frontend-with-antigravity

## Main Principle

NetGuardian should be built with agentic engineering, not casual vibe coding.

That means:

- Start from clear specs.
- Keep context inside the repository.
- Use agents to implement, but humans own intent, architecture, safety, and judgment.
- Use repeatable scaffolding, tools, evals, tests, and deployment flow.
- Treat code as changeable, but treat product intent, security boundaries, and eval criteria as source of truth.

## Day 1: New SDLC With Vibe Coding

### Knowledge Captured

The day 1 material frames the shift from syntax-first development to intent-driven development. The important distinction is between casual vibe coding and disciplined agentic engineering.

Key concepts:

- Developers express intent, architecture, and constraints.
- AI agents can implement, test, and iterate, but need a harness.
- Context engineering is a core skill.
- The SDLC changes across requirements, architecture, implementation, QA, review, deployment, and maintenance.
- The developer becomes a conductor/orchestrator of agent workflows.

### How To Apply To NetGuardian

For NetGuardian:

- Preserve project context in Markdown files.
- Create specs before large implementation.
- Keep `PROJECT_CONTEXT.md` as the high-level memory.
- Keep dedicated docs for product overview, architecture, requirements, evals, security, and demo plan.
- Make every future coding session read context first before changing implementation.

Recommended repo docs:

- `docs/project-overview.md`
- `docs/hackathon-brief.md`
- `docs/course-learning-playbook.md`
- `docs/requirements.md`
- `docs/architecture.md`
- `docs/security-model.md`
- `docs/evaluation-plan.md`
- `docs/demo-plan.md`

## Day 2: Agent Tools and Interoperability

### Knowledge Captured

The day 2 material focuses on tool and protocol interoperability.

Key concepts:

- MCP is the tool layer that connects models/agents to external systems.
- Skills are reusable playbooks for agent behavior.
- A2A enables agent-to-agent interoperability.
- A2UI/generative UI can transform structured agent output into safe interactive interfaces.
- Protocols reduce fragile custom integrations.

### How To Apply To NetGuardian

NetGuardian should use MCP as the controlled execution layer.

Recommended MCP tools for v1:

- `get_enterprise_state()`: read current endpoint, user, incident, and risk state.
- `list_active_incidents()`: show incidents requiring triage.
- `get_incident_evidence(incident_id)`: retrieve telemetry and correlated evidence.
- `propose_response_action(incident_id)`: return safe response candidates.
- `isolate_device(device_id)`: isolate a simulated endpoint after approval.
- `block_ip(ip_address)`: block suspicious outbound/inbound traffic after approval.
- `verify_incident_containment(incident_id)`: check whether the threat stopped.

Important constraint:

- Agents should not run raw shell commands or directly manipulate containers.
- Agents should reason over Enterprise State and call MCP tools only through approved interfaces.

## Day 3: Agent Security and Evaluation

### Knowledge Captured

The day 3 material focuses on securing and evaluating agentic systems.

Key concepts:

- Security checks whether the agent stayed inside its boundary.
- Evaluation checks whether the agent behavior is good enough to ship.
- A raw model becomes an agent only when wrapped in a harness with state, tools, feedback loops, and constraints.
- Trust must be continuously verified at runtime.
- Important themes include sandboxing, supply-chain defense, contextual authorization, high-stakes actions, observability, red/blue/green teaming, and behavior evaluation.

### How To Apply To NetGuardian

NetGuardian is a security product, so safety cannot be decoration. It must be visible in architecture and demo.

Required safety patterns:

- Human approval before any high-impact action.
- Tool allowlist for MCP execution.
- No secrets in code.
- No direct agent shell execution.
- Audit log for all agent reasoning summaries, proposed actions, approvals, and MCP calls.
- Explicit confidence/risk scoring before response actions.
- Verification Agent must check outcomes after action.
- Evaluation cases must cover both good behavior and unsafe behavior.

Recommended eval scenarios:

- Malware infection on `Employee-01`.
- Suspicious outbound connection to unknown IP.
- Lateral movement attempt to `FILE-01`.
- Brute-force login attempts.
- False positive where no isolation should happen.
- Prompt/tool misuse attempt where agent must refuse direct execution.

## Day 4: Human-in-the-loop, Local Evaluations, Secure Agentic Coding

### Knowledge Captured

The day 4 labs are directly relevant to NetGuardian because they combine:

- Human-in-the-loop workflows.
- Local evaluation loops.
- ADK and Agents CLI project workflow.
- Secure agentic coding.
- Threat scans, safety guards, and security testing.

### How To Apply To NetGuardian

NetGuardian's incident response flow should mirror the human-in-the-loop pattern:

```text
Incident detected
  -> Investigation Agent gathers evidence
  -> Response Agent proposes action
  -> Dashboard asks human to approve or reject
  -> MCP executes only approved action
  -> Verification Agent checks containment
```

Evaluation should be local first:

- Start with 1-2 core eval cases.
- Run agent behavior evals before expanding scope.
- Add edge cases only after the happy path works.
- Use evals for LLM behavior, not brittle unit tests that assert exact LLM wording.

Secure coding checklist:

- Validate all tool inputs.
- Restrict tool permissions.
- Keep action execution idempotent where possible.
- Record who/what approved an action.
- Add failure modes for rejected approvals, failed MCP calls, and inconclusive verification.

## Day 5: Production, Deployment, and Frontend

### Knowledge Captured

The day 5 material emphasizes spec-driven production-grade development.

Key concepts:

- Vibe coding is not vibe-in-production.
- A good spec is the architectural source of truth.
- Store specs in the repository.
- Use guardrails, sandboxing, human-in-the-loop, generated test coverage, evaluation, policy checks, and context hygiene.
- Deployability matters.
- Frontend should connect to a deployed or reproducible agent backend.

### How To Apply To NetGuardian

NetGuardian should be demoable and reproducible.

Recommended delivery path:

1. Build a local Docker Compose demo first.
2. Use SQLite for Enterprise State in v1.
3. Use FastAPI as central backend.
4. Use Streamlit as the dashboard for speed and clarity.
5. Add ADK agents after the core state/tool boundaries are clear.
6. Add MCP tools for approved response actions.
7. Add local evals for incident investigation and response recommendations.
8. Prepare Cloud Run or Agent Runtime deployment only after local demo works.

For Kaggle submission, a solid public GitHub repo with Docker Compose setup may be enough if live deployment is not feasible.

## NetGuardian Build Workflow

Use this workflow for future implementation sessions:

1. Read context:
   - `PROJECT_CONTEXT.md`
   - `docs/project-overview.md`
   - `docs/hackathon-brief.md`
   - `docs/course-learning-playbook.md`
2. Confirm the current milestone:
   - spec, scaffold, backend, Enterprise State, MCP, agents, UI, eval, deploy, writeup, or video.
3. If creating an ADK project, use Agents CLI scaffold rather than hand-rolling structure.
4. Implement in small slices:
   - data model
   - telemetry ingestion
   - incident detection
   - investigation agent
   - response proposal
   - human approval
   - MCP execution
   - verification
   - dashboard
5. Verify each slice:
   - code-level tests for deterministic logic
   - `agents-cli run` for quick agent smoke checks
   - `agents-cli eval` for agent behavior
6. Update docs after major decisions.

## Technical Patterns To Reuse

### Enterprise State First

Agents should not inspect raw Docker state as their main input. They should read Enterprise State because it includes organizational context.

### MCP As Safety Boundary

All high-impact actions must go through MCP tools with explicit schemas and validation.

### Human Approval Gate

Actions such as isolate device, disable user, or block IP require approval before execution.

### Multi-agent Separation

Keep role boundaries clear:

- Investigation Agent: evidence and root cause.
- Response Agent: safe response options and risk tradeoffs.
- Verification Agent: post-action checks.
- Coordinator: workflow sequencing.

### Eval-driven Agent Quality

Use eval cases to test:

- Correct evidence extraction.
- Reasonable response recommendation.
- Refusal of unsafe direct execution.
- Correct handling of false positives.
- Verification after approved action.

### Deployment Readiness

Every major component should be runnable locally and explainable in the README:

- FastAPI backend.
- Streamlit dashboard.
- SQLite state.
- Docker simulated endpoints.
- MCP server.
- ADK agents.

## Immediate Next Project Step

Before writing application code, create a concrete implementation spec:

- `docs/requirements.md`
- `docs/architecture.md`
- `docs/security-model.md`
- `docs/evaluation-plan.md`
- `.agents-cli-spec.md` if using Agents CLI scaffold

The first demo scenario should likely be:

```text
Employee-01 downloads malware
  -> telemetry reports suspicious process and outbound connection
  -> Enterprise State raises risk
  -> Investigation Agent explains evidence
  -> Response Agent recommends isolation
  -> human approves
  -> MCP isolates device
  -> Verification Agent confirms containment
```
