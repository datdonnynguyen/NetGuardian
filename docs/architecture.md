# NetGuardian Architecture

```mermaid
flowchart TD
    A[Docker Endpoint Simulator] --> B[Telemetry Event]
    B --> C[Python Event Dispatcher]
    C --> D[Telemetry Engine]
    D --> E[Enterprise State / Digital Twin]
    E --> F[Business Context]
    E --> G[Threat Intelligence]
    E --> H[Incident Engine]
    H --> I[Incident]
    I --> J[ADK-style Coordinator]
    J --> K[Investigation Agent]
    J --> L[Response Agent]
    J --> M[Verification Agent]
    L --> N[Human Approval]
    N --> O[MCP-style Execution Layer]
    O --> P[Docker Endpoint State]
    P --> M
    Q[Streamlit Dashboard] --> R[FastAPI Backend]
    R --> E
    R --> J
    R --> O
```

## Core Rule

Enterprise State is the single source of truth. Agents do not inspect Docker directly and do not create incidents directly.

## Services

- FastAPI backend: central API for state, incidents, recommendations, approvals, and execution.
- SQLite: local Enterprise Digital Twin.
- Streamlit dashboard: human operator interface.
- MCP-style execution module: controlled action boundary.
- Endpoint simulator: emits demo telemetry.

