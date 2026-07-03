from __future__ import annotations

import os
from typing import Any

from .database import connect, row, rows
from .docker_helper import DOCKER_SOCKET_PATH, execute_command_in_container
from .event_bus import EventDispatcher
from .incident_engine import IncidentEngine


class EnterpriseState:
    def __init__(self) -> None:
        self.incident_engine = IncidentEngine()
        self.dispatcher = EventDispatcher()
        self.dispatcher.subscribe("*", self._record_telemetry)
        self.dispatcher.subscribe("*", self._evaluate_incident)

    def ingest_event(self, event: dict[str, Any]) -> dict:
        self.dispatcher.publish(event)
        return self.get_state()

    def ingest_demo_events(self) -> dict:
        events = [
            {
                "device_id": "employee-01",
                "event_type": "process_started",
                "value": "EXCEL.EXE spawned powershell.exe from macro",
                "severity": 9,
                "details": "Alice opened Q3_Payroll_Adjustments.xlsm and a macro launched PowerShell.",
            },
            {
                "device_id": "employee-01",
                "event_type": "dns_request",
                "value": "evil-macro.example",
                "severity": 7,
                "details": "Endpoint resolved a domain from local threat intelligence.",
            },
            {
                "device_id": "employee-01",
                "event_type": "network_connection",
                "value": "203.0.113.66",
                "severity": 10,
                "details": "Outbound connection to known command-and-control infrastructure.",
            },
            {
                "device_id": "employee-01",
                "event_type": "smb_scan",
                "value": "FILE-01:445",
                "severity": 8,
                "details": "Endpoint attempted SMB discovery toward Finance file server.",
            },
        ]
        
        # Real Docker malware network simulation if socket exists
        docker_sim_msg = ""
        if os.path.exists(DOCKER_SOCKET_PATH):
            # 1. Connect to C2 server
            c2_ok, c2_out = execute_command_in_container("employee-01", ["curl", "-s", "-m", "2", "http://c2-server"])
            # 2. SMB Port scan FILE-01
            smb_ok, smb_out = execute_command_in_container("employee-01", ["nc", "-z", "-w", "2", "file-01", "445"])
            
            docker_sim_msg = " [Docker malware network simulation executed: C2 curl & SMB scan triggered]"
            with connect() as conn:
                conn.execute(
                    "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                    ("telemetry_engine", "docker_sim_network_connections", f"Triggered real network traffic on container employee-01: C2 connection status={c2_ok}, SMB port scan status={smb_ok}"),
                )

        for event in events:
            self.ingest_event(event)
            
        result = {"events_ingested": len(events), "state": self.get_state()}
        if docker_sim_msg:
            result["docker_sim"] = docker_sim_msg
        return result

    def get_state(self) -> dict:
        return {
            "users": rows("SELECT * FROM users ORDER BY id"),
            "devices": rows("SELECT * FROM devices ORDER BY id"),
            "business_assets": rows("SELECT * FROM business_assets ORDER BY id"),
            "relationships": rows("SELECT * FROM relationships ORDER BY id"),
            "telemetry_events": rows("SELECT * FROM telemetry_events ORDER BY id"),
            "threat_intel": rows("SELECT * FROM threat_intel ORDER BY indicator"),
            "incidents": rows("SELECT * FROM incidents ORDER BY id DESC"),
            "audit_logs": rows("SELECT * FROM audit_logs ORDER BY id DESC"),
        }

    def get_incident(self, incident_id: int) -> dict | None:
        incident = row("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        if not incident:
            return None
        device = row("SELECT * FROM devices WHERE id = ?", (incident["device_id"],))
        owner = row("SELECT * FROM users WHERE id = ?", (device["owner_id"],)) if device else None
        direct_relationships = rows(
            "SELECT * FROM relationships WHERE source_id IN (?, ?) OR target_id IN (?, ?)",
            (incident["device_id"], owner["id"] if owner else "", incident["device_id"], owner["id"] if owner else ""),
        )
        related_asset_ids = {rel["target_id"] for rel in direct_relationships if rel["relation"] == "has_access_to"}
        hosted_relationships: list[dict] = []
        if related_asset_ids:
            placeholders = ",".join("?" for _ in related_asset_ids)
            hosted_relationships = rows(
                f"SELECT * FROM relationships WHERE source_id IN ({placeholders})",
                tuple(sorted(related_asset_ids)),
            )
            related_asset_ids.update(rel["target_id"] for rel in hosted_relationships)
        critical_assets: list[dict] = []
        if related_asset_ids:
            placeholders = ",".join("?" for _ in related_asset_ids)
            critical_assets = rows(
                f"SELECT * FROM business_assets WHERE id IN ({placeholders}) ORDER BY criticality DESC, name",
                tuple(sorted(related_asset_ids)),
            )
        return {
            "incident": incident,
            "device": device,
            "owner": owner,
            "relationships": direct_relationships + hosted_relationships,
            "critical_assets": critical_assets,
            "evidence": rows("SELECT * FROM incident_evidence WHERE incident_id = ? ORDER BY weight DESC", (incident_id,)),
            "recommendations": rows("SELECT * FROM recommendations WHERE incident_id = ? ORDER BY id DESC", (incident_id,)),
            "approvals": rows("SELECT * FROM approvals WHERE incident_id = ? ORDER BY id DESC", (incident_id,)),
            "actions": rows("SELECT * FROM actions WHERE incident_id = ? ORDER BY id DESC", (incident_id,)),
            "telemetry_events": rows("SELECT * FROM telemetry_events WHERE device_id = ? ORDER BY id", (incident["device_id"],)),
        }

    def _record_telemetry(self, event: dict[str, Any]) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO telemetry_events(device_id, event_type, value, severity, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event["device_id"],
                    event["event_type"],
                    event["value"],
                    int(event.get("severity", 1)),
                    event.get("details", ""),
                ),
            )
            conn.execute(
                "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                ("telemetry_engine", "telemetry_ingested", f"{event['event_type']} from {event['device_id']}: {event['value']}"),
            )

    def _evaluate_incident(self, event: dict[str, Any]) -> None:
        self.incident_engine.evaluate_device(event["device_id"])
