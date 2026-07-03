# NetGuardian Evaluation

NetGuardian uses two evaluation layers.

## Deterministic Unit Tests

The unit tests in `tests/test_netguardian_core.py` validate code behavior that must never depend on model output:

- Incident creation from the Alice malware telemetry sequence.
- False-positive telemetry staying below incident threshold.
- `FILE-01` and Payroll Database modeled as critical assets.
- MCP denial when approval is missing or invalid.
- Approved isolation updating endpoint state.
- Verification confirming containment and protected critical assets.
- Response recommendation containing explainability fields.
- Follow-up analyst Q&A being audited and grounded in incident evidence.

Run:

```bash
python3 -m unittest discover -s tests
```

## Agent Behavior Evals

`eval/netguardian_eval_cases.yaml` captures behavior expectations for the future live ADK/Gemini version.

These cases should be run with Agents CLI eval once the deterministic ADK-style layer is wrapped as live ADK agents. They intentionally evaluate behavior and safety instead of asserting exact wording.

Core behaviors:

- Investigate the Alice malware incident.
- Mention known C2 evidence.
- Connect endpoint risk to Finance, `FILE-01`, and the Payroll Database.
- Recommend isolating `Employee-01`.
- Require human approval.
- Refuse approval-bypass prompts.
- Answer analyst follow-up questions from the active incident bundle.
- Verify containment and business impact after approved execution.
