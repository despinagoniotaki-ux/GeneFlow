"""
pipeline.py – Main pipeline orchestrator.
Wires all agents together and returns the final impact report dict.
"""
from __future__ import annotations
import sys, os

# Layout-agnostic imports
_here = os.path.dirname(os.path.abspath(__file__))
for _p in [
    os.path.join(_here, "..", "agents"),
    os.path.join(_here, ".."),
    _here,
]:
    _abs = os.path.normpath(_p)
    if _abs not in sys.path:
        sys.path.insert(0, _abs)

from ingest import load_all
from evidence_extractor import extract_claims
from change_detector import detect_changes
from dependency_agent import resolve_dependencies
from consistency_agent import run_consistency_checks
from impact_report_agent import generate_report


def run_pipeline(documents_folder: str) -> dict:
    docs          = load_all(documents_folder)
    all_claims    = []
    for d in docs:
        all_claims.extend(extract_claims(d))
    change_diffs  = detect_changes(docs)
    dep_links     = resolve_dependencies(docs)
    alerts        = run_consistency_checks(all_claims, change_diffs, dep_links)
    report        = generate_report(alerts)
    report["_claims_count"]      = len(all_claims)
    report["_documents_loaded"]  = len(docs)
    return report
