"""
dependency_agent.py – Dependency Agent
Resolves SOP dependencies from the registry and flags retired-version references.
"""
from __future__ import annotations
import re, uuid

# Active SOP versions (sourced from sop_registry.txt)
SOP_REGISTRY: dict[str, dict] = {
    "SOP-302": {"active": "v3", "retired": ["v2"]},
    "SOP-101": {"active": "v4", "retired": []},
    "SOP-201": {"active": "v2", "retired": []},
}

def resolve_dependencies(docs: list[dict]) -> list[dict]:
    """Return DependencyLink dicts for any retired-SOP references."""
    links: list[dict] = []
    for doc in docs:
        doc_id = doc["metadata"].get("ID", doc.get("path", "UNKNOWN"))
        text = doc.get("full_text", "")
        for sop_id, versions in SOP_REGISTRY.items():
            for retired_ver in versions["retired"]:
                pattern = rf"{re.escape(sop_id)}\s+{re.escape(retired_ver)}"
                if re.search(pattern, text, re.IGNORECASE):
                    links.append({
                        "sop_id":                sop_id,
                        "active_version":        versions["active"],
                        "retired_version":       retired_ver,
                        "referencing_documents": [doc_id],
                    })
    return links
