from __future__ import annotations

from .database import connect, init_db


def reset_demo() -> dict:
    init_db()
    with connect() as conn:
        for table in [
            "audit_logs",
            "actions",
            "approvals",
            "recommendations",
            "incident_evidence",
            "incidents",
            "telemetry_events",
            "relationships",
            "business_assets",
            "devices",
            "users",
            "threat_intel",
        ]:
            conn.execute(f"DELETE FROM {table}")

        conn.executemany(
            "INSERT INTO users(id, name, department, role) VALUES (?, ?, ?, ?)",
            [
                ("alice", "Alice Nguyen", "Finance", "Payroll Analyst"),
                ("sec-admin", "Security Admin", "Security", "SOC Lead"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO devices(id, hostname, owner_id, department, criticality, network_status, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("employee-01", "Employee-01", "alice", "Finance", "high", "online", 0),
            ],
        )
        conn.executemany(
            "INSERT INTO business_assets(id, name, asset_type, criticality, department) VALUES (?, ?, ?, ?, ?)",
            [
                ("file-01", "FILE-01", "file_server", "critical", "Finance"),
                ("payroll-db", "Payroll Database", "database", "critical", "Finance"),
            ],
        )
        conn.executemany(
            "INSERT INTO relationships(source_id, relation, target_id, description) VALUES (?, ?, ?, ?)",
            [
                ("alice", "owns", "employee-01", "Alice is the primary user of Employee-01."),
                ("employee-01", "has_access_to", "file-01", "Employee-01 can access the Finance file server."),
                ("file-01", "hosts", "payroll-db", "FILE-01 hosts the Payroll Database used by Finance."),
            ],
        )
        conn.executemany(
            """
            INSERT INTO threat_intel(indicator, indicator_type, label, confidence, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("203.0.113.66", "ip", "Known C2 Infrastructure", 95, "Command-and-control IP associated with macro malware."),
                ("evil-macro.example", "domain", "Malicious Macro Dropper", 90, "Domain used by fake Excel macro payloads."),
                ("b6f00d-macro-hash", "hash", "Finance Macro Malware", 88, "Known malicious Excel macro hash."),
            ],
        )
        conn.execute(
            "INSERT INTO audit_logs(actor, event, details) VALUES (?, ?, ?)",
            ("system", "demo_reset", "Seeded Alice finance malware isolation scenario."),
        )
    return {"status": "reset", "scenario": "alice_finance_malware"}


if __name__ == "__main__":
    print(reset_demo())
