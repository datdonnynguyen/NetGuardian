# NetGuardian - Project Context

## Purpose

This file stores the standing context for the `NetGuardian` workspace so future Codex/chat sessions can understand the project without requiring the same background to be repeated.

Current known goal from the user:

- Build and maintain project context inside this folder.
- Keep important planning, requirements, decisions, and implementation notes in Markdown so future sessions can quickly recover the working context.

## Current Repository State

As of 2026-06-28, this workspace is an initialized Git repository but does not yet contain application source code, requirements documents, or implementation files.

Observed contents:

- `.git/`
- `PROJECT_CONTEXT.md`

## Working Language

The user primarily communicates in Vietnamese.

Preferred response style:

- Use Vietnamese unless the user asks otherwise.
- Be direct, practical, and implementation-focused.
- When creating files or documentation, keep structure clear enough for future AI/chat sessions to scan quickly.

## How Future Sessions Should Use This File

At the start of a new session in this folder:

1. Read `PROJECT_CONTEXT.md`.
2. Check for additional documentation files such as `README.md`, `requirements.md`, `notes.md`, or files in a `docs/` folder.
3. Inspect the repository structure before making assumptions.
4. Preserve and update this file when project goals, requirements, architecture, or decisions change.

## Project Summary

Project name: `NetGuardian`

Detailed project description: NetGuardian is an AI-powered enterprise security platform that helps organizations detect, investigate, respond to, and verify cybersecurity incidents using coordinated AI agents.

Short description: NetGuardian is an AI-assisted enterprise security system that helps organizations detect, investigate, respond to, and verify cybersecurity incidents. It acts like a Security Analyst AI working with the security team.

Current external context:

- The user is building this project for the Kaggle Community Hackathon `AI Agents: Intensive Vibe Coding Capstone Project`.
- See `docs/hackathon-brief.md` for the summarized competition requirements, scoring criteria, deliverables, and deadline.
- See `docs/project-overview.md` for the main product concept, architecture, agent roles, and technical stack.
- See `docs/course-learning-playbook.md` for the 5-day course/lab knowledge map and how to apply it to NetGuardian.
- Current implementation includes FastAPI, SQLite, Streamlit, Docker Compose, Enterprise Digital Twin, Event Dispatcher, Incident Engine, deterministic ADK-style agents, MCP-style human-approved execution, tests, README, Kaggle writeup draft, and video script.

Core architecture:

- Docker containers simulate enterprise endpoints such as laptops, servers, and firewalls.
- Endpoints send telemetry events through a Python Event Dispatcher.
- Enterprise State acts as an Enterprise Digital Twin and single source of truth.
- Business Context and Threat Intelligence enrich incident reasoning.
- Incident Engine creates incidents deterministically; AI does not create incidents.
- ADK-style Coordinator coordinates the multi-agent workflow.
- Investigation Agent investigates incidents.
- Response Agent recommends response actions.
- Human Approval is required before dangerous actions.
- MCP-style execution layer executes approved actions against simulated endpoints.
- Verification Agent checks whether the response worked.

Primary technology stack:

- Backend: FastAPI.
- AI: Google ADK + Gemini.
- Tool layer: MCP.
- UI: Streamlit.
- Endpoint simulation: Docker containers.
- Database: SQLite.
- Deployment: Docker Compose.

## Requirements

Known requirements:

- Maintain persistent project context in this repository.
- Shape the project so it can become a valid Kaggle hackathon submission.
- Submission must include a Kaggle Writeup, media gallery, public video, and public project link.
- The project should demonstrate at least 3 course concepts such as ADK agent or multi-agent system, MCP Server, security features, deployability, Antigravity, or agent skills.
- Build NetGuardian as an enterprise security/SOC assistant, not just a chatbot that reads logs.
- Use Enterprise State as the central source of context for AI reasoning.
- Require human approval before AI-triggered dangerous actions.
- Use MCP as the execution layer instead of allowing AI to run commands directly.

Requirements to clarify:

- Exact first incident scenario for the demo.
- Final target user: SOC analyst, security engineer, small business IT admin, or executive security team.
- Scope of v1 dashboard.
- Exact MCP tools to implement first.
- UI/API expectations.
- Security, privacy, and data handling requirements.
- Which Kaggle track to enter: `Agents for Good`, `Agents for Business`, `Concierge Agents`, or `Freestyle`.

## Decisions

Confirmed decisions:

- Use Markdown files in the repository to preserve project context.
- Keep a separate hackathon brief in `docs/hackathon-brief.md`.
- Keep the main product overview in `docs/project-overview.md`.
- Keep the course/lab learning map in `docs/course-learning-playbook.md`.
- Use the concept of Enterprise State as the central system memory.
- Docker is for endpoint simulation, not the main source of intelligence.
- AI reads Enterprise State rather than directly inspecting containers.
- ADK is the agent coordinator.
- MCP is the controlled execution layer.
- Human approval gates dangerous response actions.

Open decisions:

- Application architecture.
- Detailed service architecture.
- Authentication model.
- Testing strategy.
- Public deployment environment or local-only Docker Compose demo.
- Final Kaggle track.
- Final demo format and public project link strategy.
- First demo scenario.

## Notes For Future Updates

When the user provides new background, append or merge it into this file under the correct section. If the context becomes large, split details into `docs/` files and keep this file as the high-level index.

Suggested future files:

- `README.md` for public-facing project overview and setup.
- `docs/requirements.md` for product requirements.
- `docs/architecture.md` for technical design.
- `docs/security-model.md` for human approval, MCP action boundaries, secrets, and audit behavior.
- `docs/evaluation-plan.md` for ADK/Agents CLI eval scenarios.
- `docs/demo-plan.md` for the Kaggle demo flow.
- `docs/decisions.md` for architecture decision records.
- `docs/tasks.md` for implementation checklist.
- `docs/kaggle-writeup-draft.md` for the 2,500-word Kaggle submission draft.
- `docs/video-script.md` for the 5-minute YouTube demo script.

## Hackathon Context

The user stated that the attached Kaggle page is the competition they are participating in.

Competition: `AI Agents: Intensive Vibe Coding Capstone Project`.

Deadline from attached text:

- July 7, 2026 at 4:59 PM GMT+10.
- The same text also mentions July 6, 2026 at 11:59 PM PT.

Because deadline wording appears in two time zones, future sessions should verify exact timing if close to submission.

## Latest User Request Captured

The user asked to synthesize all prepared content into a Markdown file inside this folder so future chats with this folder can understand the context and the user does not need to repeat background information many times.

Follow-up captured:

- The user clarified that the attached Kaggle hackathon page is the competition they are currently joining.
- The user provided the main NetGuardian project concept: an AI-powered enterprise security platform using Enterprise State, telemetry, ADK-coordinated agents, human approval, MCP execution, Docker endpoint simulation, FastAPI, Streamlit, SQLite, and Docker Compose.
- The user clarified that `knowledge/` contains the 5-day course materials and provided the corresponding day-by-day codelabs. Future work should apply these techniques: spec-driven/agentic engineering, Antigravity/Agents CLI workflow, MCP, Skills, ADK, human-in-the-loop, local evaluations, secure agentic coding, deployment, and frontend integration.
- Implementation started from the final accepted plan: NetGuardian as an Enterprise Security Operating System for the Alice Finance malware isolation scenario.
