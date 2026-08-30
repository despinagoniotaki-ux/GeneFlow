"""
impact_report_agent.py – Impact Report Agent
Synthesises all alerts into an executive JSON impact report.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

def generate_report(alerts: list[dict]) -> dict:
    critical = sum(1 for a in alerts if a["severity"] == "CRITICAL")
    high     = sum(1 for a in alerts if a["severity"] == "HIGH")
    medium   = sum(1 for a in alerts if a["severity"] == "MEDIUM")
    low      = sum(1 for a in alerts if a["severity"] == "LOW")

    return {
        "report_id":      f"RPT-{uuid.uuid4().hex[:8].upper()}",
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "total_alerts":   len(alerts),
        "critical_count": critical,
        "high_count":     high,
        "medium_count":   medium,
        "low_count":      low,
        "executive_summary": (
            f"{len(alerts)} compliance issues detected across the GeneFlow submission package. "
            f"{critical} CRITICAL safety findings require immediate action before FIH dosing. "
            f"{high} HIGH-severity regulatory gaps and {medium} MEDIUM procedural discrepancies identified."
        ),
        "alerts": alerts,
    }
