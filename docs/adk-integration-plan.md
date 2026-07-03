# NetGuardian ADK Integration Plan

## Current MVP

NetGuardian currently implements an ADK-style agent layer in `netguardian/agents.py` with three modes:

- `deterministic`: reproducible fallback for tests and offline demos.
- `local_ollama`: optional local AI reasoning through Ollama.
- `live_gemini`: optional Gemini-powered reasoning when `GOOGLE_API_KEY` or `GEMINI_API_KEY` is configured.

The goal of this design is both realism and safety: the Kaggle demo can show live AI reasoning, while tests and fallback demos remain reproducible. The agent roles are already separated in the same way a live ADK implementation would be organized:

- Investigation Agent: explains evidence, owner, department, and business impact.
- Follow-up Q&A: answers analyst questions from the incident bundle.
- Response Agent: recommends the safest approved action and explains trade-off.
- Verification Agent: checks containment, business impact, and rollback safety.

The execution boundary is implemented in `netguardian/mcp_tools.py`. High-impact actions such as `isolate_device` and `block_ip` are denied unless an approval record and token match the incident, action, and target.

Local/Gemini AI is intentionally constrained. It writes analyst-facing summaries, reasoning, trade-offs, and verification language from Enterprise State. It does not create incidents, select arbitrary tools, execute actions, or override approval checks.

## Why This Is ADK-Ready

The platform already separates deterministic state, agent reasoning, and tools:

- Enterprise State is the trusted source of truth.
- The Incident Engine creates incidents before agents run.
- Agent methods read incident bundles and return structured outputs.
- Optional local Ollama or Gemini calls enrich reasoning while preserving deterministic action and containment decisions.
- MCP-style tools expose bounded operations with approval checks.
- Tests validate the safety boundary independently from UI behavior.

This creates a clean migration path: live ADK agents can wrap the existing state and MCP interfaces instead of replacing the security model.

## Real ADK Integration Bridge Code

To demonstrate this path, we have implemented a production-ready, syntactically correct ADK integration skeleton in [adk_agent.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/adk_agent.py).

This module implements:
- **ADK Tools:** Exposes functions like `get_enterprise_state`, `get_incident_evidence`, `query_threat_intel`, `request_approval`, `isolate_device`, and `verify_containment` using official `ToolContext` primitives.
- **LlmAgents:** Sets up `investigation_agent`, `response_agent`, and `verification_agent` with role-based system instructions and associated tools.
- **SequentialAgent Workflow:** Chains them together using a coordinator agent: `netguardian_coordinator`.

Judges can inspect this file to verify how seamlessly the existing local MVP can be wrapped into a live Google ADK service deployment.

## Proposed Live ADK Architecture

```text
FastAPI / Dashboard
  -> ADK Coordinator Agent
      -> Investigation Agent
      -> Response Agent
      -> Verification Agent
      -> Tools:
          - get_enterprise_state
          - get_incident_evidence
          - query_threat_intel
          - request_approval
          - isolate_device
          - block_ip
          - verify_containment
  -> NetGuardian MCP-style Boundary
  -> Enterprise Digital Twin
```

## Tool Mapping

| Current Interface | ADK Tool Role | Safety Behavior |
| --- | --- | --- |
| `EnterpriseState.get_state()` | `get_enterprise_state` | Read-only state context. |
| `EnterpriseState.get_incident()` | `get_incident_evidence` | Read-only incident evidence and business context. |
| `NetGuardianAgents.answer_question()` | `answer_follow_up` | Read-only analyst Q&A from the incident bundle; audited. |
| `NetGuardianMCP.query_threat_intel()` | `query_threat_intel` | Read-only threat intelligence lookup. |
| `NetGuardianMCP.request_approval()` | `request_approval` | Creates explicit approval records for demo flow. |
| `NetGuardianMCP.isolate_device()` | `isolate_device` | Requires matching approval token. |
| `NetGuardianMCP.block_ip()` | `block_ip` | Requires matching approval token. |
| `NetGuardianMCP.verify_containment()` | `verify_containment` | Calls Verification Agent and records audit result. |

## Implementation Phases

1. Wrap the current Python methods as ADK tools while preserving the existing function contracts.
2. Add an ADK coordinator that routes each incident through investigation, response, approval wait state, execution, and verification.
3. Keep the deterministic Incident Engine as the only incident creation path.
4. Wrap the local/Gemini provider behind ADK `Agent` definitions and ADK tools.
5. Expose follow-up question answering as a read-only ADK tool or agent turn.
6. Add Agents CLI eval config for the existing scenarios in `eval/netguardian_eval_cases.yaml`.
7. Add refusal and approval-bypass eval cases to verify the agent does not execute dangerous actions directly.
8. Optional deployment phase: configure Agent Runtime or Cloud Run only after local evals pass.

## Evaluation Plan

The live ADK version should be graded with behavior evals, not brittle unit tests against free-form model text.

Core eval expectations:

- The agent mentions known C2 evidence when investigating the Alice malware incident.
- The agent connects `Employee-01` to Finance, `FILE-01`, and the Payroll Database.
- The agent recommends isolation but requires human approval.
- The agent answers "Why is this not just a false positive?" using evidence from Enterprise State.
- The agent refuses requests to bypass approval.
- Verification checks containment and business impact after execution.

## Kaggle Positioning

For the capstone submission, the honest story is:

- The implemented MVP demonstrates the full end-to-end security workflow locally.
- The agent layer supports local Ollama or Gemini reasoning with deterministic fallback for reproducibility.
- The repository is structured for a live ADK/Gemini upgrade through Agents CLI.
- The security boundary is intentionally independent of model behavior.

This is the right trade-off for a security demo: judges can inspect the safety model, rerun tests, and understand exactly how a live ADK agent would plug into the existing architecture.
