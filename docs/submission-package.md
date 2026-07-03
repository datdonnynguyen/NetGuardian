# NetGuardian Kaggle Submission Package

## Submission Summary

Project title: NetGuardian: An Enterprise Security Operating System Powered by AI Agents

Track: Agents for Business

One-line description: NetGuardian turns endpoint telemetry into a safe, explainable, human-approved incident response workflow using an Enterprise Digital Twin, ADK-style agents, and MCP-style controlled execution.

## Required Links

- Public code repository: [To be added by user during GitHub publication] (e.g. `https://github.com/yourusername/NetGuardian`)
- Public demo video: [To be added by user after video upload] (e.g. YouTube or Loom link under 5 minutes)
- Kaggle writeup: use `docs/kaggle-writeup-draft.md`.
- Media gallery assets: use the architecture diagram and dashboard screenshots in `docs/media/`.

## Recommended Media Gallery

1. Architecture diagram showing telemetry, Enterprise Digital Twin, Incident Engine, ADK-style agents, human approval, MCP-style execution, and verification: `docs/media/netguardian-architecture.svg`.
2. Dashboard overview with incident case selected: `docs/media/01-dashboard-overview.jpg`.
3. Evidence timeline showing the Alice malware telemetry: `docs/media/02-evidence-timeline.jpg`.
4. AI Investigation and Response view showing evidence, reasoning, recommendation, trade-off, confidence, and required approval: `docs/media/03-ai-investigation-response.jpg`.
5. Approval and MCP execution view showing denied unapproved action and approved isolation: `docs/media/04-approval-mcp-execution.jpg`.
6. Verification and audit trail showing containment and `FILE-01` / Payroll Database safety: `docs/media/05-verification-audit.jpg`.

## Demo Proof Points

- Reset demo produces a clean deterministic baseline.
- Running Alice malware events creates one high-risk incident.
- `Employee-01` is the affected endpoint.
- `FILE-01` and Payroll Database are critical business assets, not ordinary endpoints.
- The Response Agent recommends isolating `Employee-01`.
- Optional local Ollama or Gemini mode can generate analyst-facing reasoning from the incident bundle.
- The `Ask Investigation Agent` flow answers a custom analyst question without changing deterministic security decisions.
- Unapproved isolation is denied.
- Approved isolation succeeds through the MCP-style boundary.
- Verification confirms containment and protected critical assets.

## Local Verification Status

Last verified locally:

- Unit tests: 9 passing.
- Compile check: clean for `netguardian`, `endpoint_simulator`, and `tests`.
- Docker Compose config: valid.
- Agents CLI: project detected as `netguardian`, prototype mode, no deployment target configured.
- Runtime servers: API/dashboard were not running at the beginning of the latest verification session.

Runtime note: API and dashboard servers may not be running by default. Start them with:

```bash
NETGUARDIAN_AI_MODE=live NETGUARDIAN_AI_PROVIDER=ollama NETGUARDIAN_OLLAMA_URL=http://127.0.0.1:11434 NETGUARDIAN_OLLAMA_MODEL=qwen2.5:7b .venv/bin/uvicorn netguardian.api:app --host 127.0.0.1 --port 8000
.venv/bin/streamlit run netguardian/dashboard.py --server.address 127.0.0.1 --server.port 8501
```

Latest local AI verification:

- Ollama is installed locally.
- `qwen2.5:7b` is available locally.
- `/agent-mode` reports `active: local_ollama`.
- Investigation and recommendation endpoints return `mode: local_ollama` with `model: qwen2.5:7b`.

## Final Submission Checklist

- [ ] Add public GitHub or Kaggle notebook link.
- [ ] Record and publish a video under five minutes.
- [x] Add at least three media gallery images.
- [x] Add a polished architecture diagram image.
- [ ] Update the writeup with final repository and video links.
- [x] Run unit tests: `python3 -m unittest discover -s tests` (9 tests passed).
- [x] Run compile check: `.venv/bin/python -m compileall netguardian tests` (clean compilation).
- [x] Run behavior evaluation runner: `.venv/bin/python eval/run_evals.py` (100% accuracy score).
- [x] Run `docker compose config` (valid config verified).
- [x] Smoke test `POST /incidents/{incident_id}/ask` with analyst follow-up questions.
- [x] Verify local Ollama mode with `qwen2.5:7b`.
- [ ] Run `./run_demo.sh` to quickly start local servers.
- [ ] If Docker Desktop is available, run `docker compose up --build` and smoke test the dashboard.
