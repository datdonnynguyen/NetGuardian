from __future__ import annotations

from .database import connect, row, rows

INCIDENT_THRESHOLD = 70


class IncidentEngine:
    def evaluate_device(self, device_id: str) -> dict:
        device = row("SELECT * FROM devices WHERE id = ?", (device_id,))
        if not device:
            return {"created": False, "reason": "unknown_device"}

        events = rows("SELECT * FROM telemetry_events WHERE device_id = ? ORDER BY id", (device_id,))
        relationships = rows("SELECT * FROM relationships WHERE source_id = ?", (device_id,))
        risk, evidence = self._score(device, events, relationships)

        with connect() as conn:
            conn.execute("UPDATE devices SET risk_score = ? WHERE id = ?", (risk, device_id))
            existing = conn.execute(
                "SELECT * FROM incidents WHERE device_id = ? AND status != 'closed'",
                (device_id,),
            ).fetchone()
            if risk < INCIDENT_THRESHOLD:
                return {"created": False, "risk_score": risk, "threshold": INCIDENT_THRESHOLD}
            if existing:
                incident_id = int(existing["id"])
                conn.execute(
                    "UPDATE incidents SET risk_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (risk, incident_id),
                )
                conn.execute("DELETE FROM incident_evidence WHERE incident_id = ?", (incident_id,))
            else:
                cur = conn.execute(
                    """
                    INSERT INTO incidents(device_id, title, status, risk_score, business_impact, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id,
                        "High-risk malware activity on Finance endpoint",
                        "active",
                        risk,
                        "Finance endpoint has access to payroll systems; containment protects payroll data.",
                        "incident_engine",
                    ),
                )
                incident_id = int(cur.lastrowid)
                conn.execute(
                    "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
                    ("incident_engine", "incident_created", f"Incident {incident_id} created with risk {risk}."),
                )
            for item in evidence:
                conn.execute(
                    """
                    INSERT INTO incident_evidence(incident_id, evidence_type, summary, weight, source_event_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        item["type"],
                        item["summary"],
                        item["weight"],
                        item.get("source_event_id"),
                    ),
                )
        return {"created": True, "incident_id": incident_id, "risk_score": risk, "evidence": evidence}

    def _score(self, device: dict, events: list[dict], relationships: list[dict]) -> tuple[int, list[dict]]:
        risk = 0
        evidence: list[dict] = []
        for event in events:
            event_type = event["event_type"]
            value = event["value"].lower()
            if event_type == "process_started" and ("powershell" in value or "macro" in value):
                risk += 40
                evidence.append(
                    {
                        "type": "malware_process",
                        "summary": f"Suspicious process observed: {event['value']}",
                        "weight": 40,
                        "source_event_id": event["id"],
                    }
                )
            if event_type == "network_connection":
                intel = row("SELECT * FROM threat_intel WHERE indicator = ?", (event["value"],))
                if intel:
                    risk += 30
                    evidence.append(
                        {
                            "type": "known_c2",
                            "summary": f"{event['value']} matches threat intel: {intel['label']}",
                            "weight": 30,
                            "source_event_id": event["id"],
                        }
                    )
            if event_type == "smb_scan":
                risk += 20
                evidence.append(
                    {
                        "type": "lateral_movement",
                        "summary": f"SMB scan activity detected toward {event['value']}",
                        "weight": 20,
                        "source_event_id": event["id"],
                    }
                )
        if device["department"] == "Finance":
            risk += 10
            evidence.append(
                {
                    "type": "business_context",
                    "summary": "Device belongs to Finance, increasing business impact.",
                    "weight": 10,
                    "source_event_id": None,
                }
            )
        if any(rel["relation"] == "has_access_to" and rel["target_id"] == "file-01" for rel in relationships):
            risk += 10
            evidence.append(
                {
                    "type": "payroll_access",
                    "summary": "Device can access FILE-01, which hosts payroll data.",
                    "weight": 10,
                    "source_event_id": None,
                }
            )
        return min(risk, 100), evidence

