"""
evidence_extractor.py – Evidence Extractor Agent
Parses document sections into atomic EvidenceClaim dicts.
Uses a 100-character context window to disambiguate noael from dose values.
"""
from __future__ import annotations
import re, uuid
from typing import Any

# Regex patterns: (parameter_name, pattern, unit)
_PATTERNS: list[tuple[str, str, str]] = [
    ("sample_size",   r"n\s*=\s*(\d+)",                                    "participants"),
    ("noael",         r"noael[^.\n]{0,100}?([\d.]+e[\d+]+)\s*vg/kg",       "vg/kg"),
    ("dose",          r"(?:starting\s+dose|mrsd|dose)[^.\n]{0,100}?([\d.]+e[\d+]+)\s*vg/kg", "vg/kg"),
    ("assay_version", r"AM-001\s+(v\d+)",                                    "version"),
    ("sop_version",   r"SOP-(\d+)\s+(v\d+)",                                "version"),
    ("vector_type",   r"\b(scAAV-hFIX|rAAV-hFIX)\b",                        "label"),
]

def extract_claims(doc: dict) -> list[dict]:
    claims: list[dict] = []
    doc_id = doc["metadata"].get("ID", doc.get("path", "UNKNOWN"))

    for sec in doc.get("sections", []):
        text = sec["content"]
        text_lower = text.lower()

        for param, pattern, unit in _PATTERNS:
            # Special handling: use full text for noael/dose to avoid false positives
            search_text = text_lower if param not in ("noael", "dose") else text_lower
            for m in re.finditer(pattern, search_text, re.IGNORECASE):
                # For sop_version, value is "SOP-{1} {2}"
                if param == "sop_version":
                    value = f"SOP-{m.group(1)} {m.group(2)}"
                else:
                    value = m.group(1)

                # Extract raw quote (100-char window)
                start = max(0, m.start() - 20)
                end   = min(len(text), m.end() + 60)
                raw_quote = text[start:end].strip()

                claims.append({
                    "claim_id":    str(uuid.uuid4()),
                    "document_id": doc_id,
                    "section":     sec["section"],
                    "parameter":   param,
                    "value":       value,
                    "unit":        unit,
                    "raw_quote":   raw_quote,
                })

    return claims
