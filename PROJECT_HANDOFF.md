# NetGuardian Project Handoff

## Read This First

This document is the single handoff point for continuing NetGuardian in a new conversation.

**Conversation Rules:**
- Speak to the user in **Vietnamese**.
- Keep all project artifacts in **English** (code, comments, README, docs, dashboard UI, API names, tests, Kaggle writeup, and video scripts).

**Recommended reading order in a new conversation:**
1. `PROJECT_HANDOFF.md` (This file)
2. `docs/submission-package.md`
3. `docs/adk-integration-plan.md`
4. `docs/kaggle-writeup-draft.md`

---

## Current Status (All Phase 1 & Phase 2 Enhancements Completed)

NetGuardian has been upgraded from a mock simulation to a **safe-by-design cyber range sandbox** supporting real network containment and AI behavior evaluations.

### Completed Accomplishments:

1. **Physical Docker Network Isolation:**
   - Updated `docker-compose.yml` to define lightweight sandbox nodes: `employee-01` (Alice), `file-01` (Finance File Server), and `c2-server` (Hacker C2).
   - Created [docker_helper.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/docker_helper.py) executing raw HTTP calls over Unix Sockets directly to `/var/run/docker.sock` to avoid external dependencies.
   - Integrated container disconnection inside `isolate_device` ([mcp_tools.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/mcp_tools.py)).
   - Integrated network connection status checking inside `verify` ([agents.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/agents.py)).
   - Built-in **SQLite Fallback mode**: if Docker socket is not present (running local venv), it logs warnings and falls back dynamically to SQLite database status without crashing.

2. **Real Malware Network Simulation:**
   - Triggered physical `curl` outbound calls and `nc` port scans directly from container `employee-01` to `c2-server` and `file-01` via Docker Exec API inside `ingest_demo_events` ([enterprise_state.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/enterprise_state.py)).

3. **Behavior Evaluation Harness:**
   - Built [run_evals.py](file:///Users/nguyendat/Documents/NetGuardian/eval/run_evals.py) dynamically testing 5 compliance cases against a running local API.
   - Achieved **100% Accuracy Score (5/5 cases passed)** on local Ollama `qwen2.5:7b`.
   - Solved state-leakage by performing clean database resets before each evaluation test case.

4. **Safety Input Guardrails (Prompt Injection Defense):**
   - Implemented an Input Security Guardrail in `answer_question` ([agents.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/agents.py)) to detect attempts to bypass/override approvals, instantly returning a structured SOC refusal message.
   - Verified by unit tests and eval harnesses.

5. **Visual Asset Flow Graph & Incident Audits:**
   - Created a dynamic HTML/CSS visual relationship tree visualizer under the **Enterprise Digital Twin** tab.
   - Added a **"Download SOC Incident Audit Report"** button compile-generating Markdown audit logs at `/incidents/{incident_id}/report` and downloadable directly on Streamlit.

6. **ADK Integration Skeleton:**
   - Created [adk_agent.py](file:///Users/nguyendat/Documents/NetGuardian/netguardian/adk_agent.py) exposing tools and role agents using official Google ADK primitives to guide cloud deployments.

---

## Local Verification Status

- **Unit Tests:** `python -m unittest discover -s tests` ➔ **9/9 tests passed**.
- **Behavior Evals:** `python eval/run_evals.py` ➔ **100% passed (5/5 cases)**.
- **Compilation:** `.venv/bin/python -m compileall netguardian tests` ➔ **Clean**.
- **Local Services:** Currently running on local ports 8000 and 8501 via `./run_demo.sh` using SQLite Fallback (since Docker Desktop is inactive).

---

## Next Steps for the New Conversation

The codebase is fully polished. The next task is for the user to publish and submit the solution:

1. **Guide User in Packaging and Submitting:**
   - Help user publish the repository to a **Public GitHub repository**.
   - Guide user on recording a **Product Demo Video** (under 5 minutes) showing the Streamlit UI, local Ollama response, Prompt Injection block, and containment verification.
   - Direct user on completing the Kaggle submission using `docs/kaggle-writeup-draft.md`, `docs/media/` assets, and final repository/video links.

2. **Docker Containment Testing:**
   - If the user turns on **Docker Desktop**, help them run:
     ```bash
     kill $(lsof -t -i:8000 -i:8501) || true
     docker compose down -v
     docker compose up --build
     ```
     Verify that the container `employee-01` is physically detached from `netguardian_default` using:
     ```bash
     docker network inspect netguardian_default
     ```
