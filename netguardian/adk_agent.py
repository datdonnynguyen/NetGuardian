"""NetGuardian Official ADK Agent Definition Bridge

This file provides the production-ready implementation skeleton for migrating
NetGuardian's simulated ADK-style agents into live, fully-managed Google Agent
Development Kit (ADK) agents.

It defines:
1. Core Platform Tools mapping directly to Enterprise State & MCP actions.
2. Distinct Agent Roles (Investigation, Response, and Verification).
3. A Sequential Coordination Agent to orchestrate the containment workflow.
"""

from __future__ import annotations

import json
from typing import Any

# Import official ADK SDK primitives (available when deployed with google-agents-cli)
try:
    from google.adk.agents import Agent, SequentialAgent
    from google.adk.tools import ToolContext
except ImportError:
    # Safe fallback wrappers for local compile check without live ADK package installed
    class Agent:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
    class SequentialAgent:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
    class ToolContext:
        pass


# =====================================================================
# 1. Platform Tools (Mapped to Enterprise State & MCP)
# =====================================================================

def get_enterprise_state(tool_context: ToolContext) -> dict[str, Any]:
    """Reads the complete Enterprise Digital Twin state, including users,

    devices, assets, telemetry events, and audit logs.

    Returns:
        A dictionary containing the current database tables.
    """
    # Under a live ADK runner, tool_context provides state or DB connection hooks
    from .enterprise_state import EnterpriseState
    return EnterpriseState().get_state()


def get_incident_evidence(incident_id: int, tool_context: ToolContext) -> dict[str, Any]:
    """Retrieves all evidence, timelines, affected endpoint details,

    and business relationships for a specific incident case.

    Args:
        incident_id: The integer ID of the SOC incident.

    Returns:
        The incident bundle containing device, owner, and telemetry events.
    """
    from .enterprise_state import EnterpriseState
    return EnterpriseState().get_incident(incident_id) or {"error": "incident_not_found"}


def query_threat_intel(indicator: str, tool_context: ToolContext) -> list[dict[str, Any]]:
    """Checks the local Threat Intelligence database for a specific indicator

    (IP address, domain name, or file hash) to identify known malicious indicators.

    Args:
        indicator: The IP address, domain, or file hash to check.

    Returns:
        A list of matching threat intelligence entries.
    """
    from .mcp_tools import NetGuardianMCP
    return NetGuardianMCP().query_threat_intel(indicator)


def request_approval(incident_id: int, action: str, target_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Creates a formal human approval request record for high-impact actions

    and returns a unique approval ID and token.

    Args:
        incident_id: The incident ID requesting action.
        action: The name of the action (e.g. 'isolate_device').
        target_id: The ID of the target device or asset.

    Returns:
        A dictionary containing 'approval_id', 'token', and status.
    """
    from .mcp_tools import NetGuardianMCP
    return NetGuardianMCP().request_approval(incident_id, action, target_id)


def isolate_device(incident_id: int, device_id: str, approval_id: int, token: str, tool_context: ToolContext) -> dict[str, Any]:
    """Isolates a compromised device from the network. This action is guarded

    by an MCP approval gate and requires a matching approval ID and token.

    Args:
        incident_id: The incident ID authorizing containment.
        device_id: The hostname/ID of the device to isolate.
        approval_id: The valid human approval ID.
        token: The corresponding approval security token.

    Returns:
        A dictionary containing the execution status and network status.
    """
    from .mcp_tools import NetGuardianMCP
    return NetGuardianMCP().isolate_device(incident_id, device_id, approval_id, token)


def verify_containment(incident_id: int, tool_context: ToolContext) -> dict[str, Any]:
    """Invokes the Verification Agent to confirm that containment was successfully

    completed, critical database assets are protected, and audit logs are recorded.

    Args:
        incident_id: The incident ID to verify.

    Returns:
        The verification results including containment state and business impact.
    """
    from .mcp_tools import NetGuardianMCP
    return NetGuardianMCP().verify_containment(incident_id)


# =====================================================================
# 2. ADK Agent Definitions
# =====================================================================

# Investigation Agent: Explains telemetry evidence and business impact
investigation_agent = Agent(
    name="investigation_agent",
    model="gemini-2.0-flash",
    instruction="""You are NetGuardian's Lead Investigation Agent.
Analyze the incident evidence and digital twin relationships.
Explain why the observed process, network connections, and scanning events are suspicious.
Call out who owns the device, their department, and what critical business assets are at risk.
Always keep security-critical details grounded in the retrieved facts.
""",
    tools=[get_incident_evidence, query_threat_intel],
)

# Response Agent: Formulates safe response recommendations and trade-offs
response_agent = Agent(
    name="response_agent",
    model="gemini-2.0-flash",
    instruction="""You are NetGuardian's Response Agent.
Formulate a containment recommendation based on the incident findings.
The only allowed response is 'isolate_device' on the affected endpoint.
Explain the trade-offs (operational impact vs security isolation).
State clearly that this is a high-impact action requiring human approval,
and call request_approval to generate the approval tokens.
""",
    tools=[request_approval, isolate_device],
)

# Verification Agent: Audits the final state of critical infrastructure
verification_agent = Agent(
    name="verification_agent",
    model="gemini-2.0-flash",
    instruction="""You are NetGuardian's Verification Agent.
Verify that containment actions succeeded.
Confirm that the compromised endpoint's network status is set to 'isolated'.
Inspect the access graph and confirm that critical business servers (FILE-01)
and database assets (Payroll Database) remain protected and online.
""",
    tools=[get_incident_evidence],
)


# =====================================================================
# 3. Multi-Agent Coordinator Workflow
# =====================================================================

# Sequential Agent pipelines the incident response process
netguardian_coordinator = SequentialAgent(
    name="netguardian_coordinator",
    description="Orchestrates the investigation, response recommendation, approval gate, and verification loop.",
    sub_agents=[investigation_agent, response_agent, verification_agent],
)
