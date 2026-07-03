# NetGuardian Security Model

## Boundaries

- AI can explain and recommend, but cannot execute high-impact actions.
- MCP-style tools are the only execution boundary.
- Docker endpoints are simulation targets, not reasoning sources.
- Enterprise State is the only source for agent reasoning.

## Approval Rules

- `isolate_device` requires an approved approval record.
- `block_ip` requires an approved approval record.
- Rejected or pending approvals must not execute.
- Every execution attempt is recorded in the audit log.

## Safe Demo Behavior

- The demo uses local simulated telemetry and local threat intelligence.
- No real host network changes are made.
- No secrets are required for the deterministic fallback path.

