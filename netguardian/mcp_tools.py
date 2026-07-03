from __future__ import annotations

import os
import secrets

from .database import connect, row, rows
from .docker_helper import DOCKER_SOCKET_PATH, disconnect_container_from_network
from .enterprise_state import EnterpriseState


class NetGuardianMCP:
    def __init__(self) -> None:
        self.state = EnterpriseState()

    def get_enterprise_state(self) -> dict:
        return self.state.get_state()

    def get_incident_evidence(self, incident_id: int) -> dict:
        return self.state.get_incident(incident_id) or {"error": "incident_not_found"}

    def query_threat_intel(self, indicator: str | None = None) -> list[dict]:
        if indicator:
            return rows("SELECT * FROM threat_intel WHERE indicator = ?", (indicator,))
        return rows("SELECT * FROM threat_intel ORDER BY indicator")

    def request_approval(self, incident_id: int, action: str, target_id: str, approver: str = "Security Admin") -> dict:
        token = secrets.token_urlsafe(16)
        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO approvals(incident_id, action, target_id, status, approver, token)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (incident_id, action, target_id, "approved", approver, token),
            )
            approval_id = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                (approver, "action_approved", f"Approved {action} on {target_id} for incident {incident_id}."),
            )
        return {"approval_id": approval_id, "token": token, "status": "approved"}

    def reject_action(self, incident_id: int, action: str, target_id: str, approver: str = "Security Admin") -> dict:
        token = secrets.token_urlsafe(16)
        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO approvals(incident_id, action, target_id, status, approver, token)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (incident_id, action, target_id, "rejected", approver, token),
            )
            approval_id = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                (approver, "action_rejected", f"Rejected {action} on {target_id} for incident {incident_id}."),
            )
        return {"approval_id": approval_id, "token": token, "status": "rejected"}

    def isolate_device(self, incident_id: int, device_id: str, approval_id: int, token: str) -> dict:
        approved = self._approval_valid(approval_id, token, incident_id, "isolate_device", device_id)
        if not approved:
            self._record_action(incident_id, "isolate_device", device_id, "denied", "Missing or invalid approval.")
            return {"status": "denied", "reason": "approval_required"}
        
        # Physical Docker Network Isolation
        docker_msg = ""
        if os.path.exists(DOCKER_SOCKET_PATH):
            net_name = os.getenv("NETGUARDIAN_DOCKER_NETWORK", "netguardian_default")
            if disconnect_container_from_network(net_name, device_id):
                docker_msg = f" Physically disconnected container '{device_id}' from network '{net_name}'."
            else:
                docker_msg = " Docker isolation failed (network or container not found)."
        else:
            docker_msg = " (SQLite fallback mode, Docker socket not found)"

        with connect() as conn:
            conn.execute("UPDATE devices SET network_status = 'isolated' WHERE id = ?", (device_id,))
            conn.execute("UPDATE incidents SET status = 'responding', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (incident_id,))
        self._record_action(incident_id, "isolate_device", device_id, "succeeded", f"Device network status set to isolated.{docker_msg}")
        return {"status": "succeeded", "device_id": device_id, "network_status": "isolated"}

    def block_ip(self, incident_id: int, ip_address: str, approval_id: int, token: str) -> dict:
        approved = self._approval_valid(approval_id, token, incident_id, "block_ip", ip_address)
        if not approved:
            self._record_action(incident_id, "block_ip", ip_address, "denied", "Missing or invalid approval.")
            return {"status": "denied", "reason": "approval_required"}
        self._record_action(incident_id, "block_ip", ip_address, "succeeded", "IP block recorded in demo control plane.")
        return {"status": "succeeded", "ip_address": ip_address}

    def verify_containment(self, incident_id: int) -> dict:
        from .agents import NetGuardianAgents

        return NetGuardianAgents().verify(incident_id)

    def _approval_valid(self, approval_id: int, token: str, incident_id: int, action: str, target_id: str) -> bool:
        approval = row(
            """
            SELECT * FROM approvals
            WHERE id = ? AND token = ? AND incident_id = ? AND action = ? AND target_id = ? AND status = 'approved'
            """,
            (approval_id, token, incident_id, action, target_id),
        )
        return approval is not None

    def _record_action(self, incident_id: int, action: str, target_id: str, status: str, result: str) -> None:
        with connect() as conn:
            conn.execute(
                "INSERT INTO actions(incident_id, action, target_id, status, result) VALUES (?, ?, ?, ?, ?)",
                (incident_id, action, target_id, status, result),
            )
            conn.execute(
                "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                ("mcp_server", f"mcp_{status}", f"{action} on {target_id}: {result}"),
            )

