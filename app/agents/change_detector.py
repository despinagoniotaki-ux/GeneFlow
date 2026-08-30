"""
change_detector.py – Change Detector Agent
Resolves the approved analytical method version and flags deprecated usages.
"""
from __future__ import annotations
import re, uuid

# Approved versions derived from SOP-AV-010
APPROVED_METHODS: dict[str, str] = {
    "AM-001": "v2",
}

def detect_changes(docs: list[dict]) -> list[dict]:
    """Return list of ChangeDiff dicts for any deprecated method reference."""
    diffs: list[dict] = []
    for doc in docs:
        doc_id = doc["metadata"].get("ID", doc.get("path", "UNKNOWN"))
        text = doc.get("full_text", "")
        for method, approved_ver in APPROVED_METHODS.items():
            for m in re.finditer(rf"{re.escape(method)}\s+(v\d+)", text, re.IGNORECASE):
                detected = m.group(1).lower()
                if detected != approved_ver.lower():
                    diffs.append({
                        "diff_id":            str(uuid.uuid4()),
                        "method_id":          method,
                        "approved_version":   approved_ver,
                        "detected_version":   detected,
                        "affected_documents": [doc_id],
                    })
    return diffs
