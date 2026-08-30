"""
tests/test_agents.py
Pytest suite: 9 tests covering ingestion, extraction, and all 6 planted inconsistencies.
"""
import sys, os, pytest

# Resolve paths regardless of CWD
_tests_dir   = os.path.dirname(os.path.abspath(__file__))
_root        = os.path.dirname(_tests_dir)
_agents_dir  = os.path.join(_root, "app", "agents")
_backend_dir = os.path.join(_root, "app", "backend")
_docs_dir    = os.path.join(_root, "documents")

for _p in [_agents_dir, _backend_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ingest import load_document, load_all
from evidence_extractor import extract_claims
from change_detector import detect_changes
from dependency_agent import resolve_dependencies
from consistency_agent import run_consistency_checks
from impact_report_agent import generate_report

# ── Helpers ────────────────────────────────────────────────────────────────

def _load(filename: str) -> dict:
    return load_document(os.path.join(_docs_dir, filename))

def _all_docs():
    return load_all(_docs_dir)

def _full_pipeline():
    docs       = _all_docs()
    all_claims = []
    for d in docs:
        all_claims.extend(extract_claims(d))
    diffs  = detect_changes(docs)
    links  = resolve_dependencies(docs)
    alerts = run_consistency_checks(all_claims, diffs, links)
    return all_claims, diffs, links, alerts

# ── Test 1: Document ingestion ─────────────────────────────────────────────

def test_document_ingestion():
    doc = _load("clinical_protocol.txt")
    assert doc["metadata"]["ID"] == "CP-2024-001"
    assert len(doc["sections"]) >= 3
    assert doc["full_text"]

# ── Test 2: Evidence extraction ────────────────────────────────────────────

def test_evidence_extraction():
    doc    = _load("clinical_protocol.txt")
    claims = extract_claims(doc)
    params = [c["parameter"] for c in claims]
    assert "sample_size" in params, "Sample size claim not extracted"
    assert "dose" in params, "Dose claim not extracted"

# ── Test 3: Alert 1 – Sample Size Conflict ─────────────────────────────────

def test_alert_sample_size_conflict():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "SAMPLE_SIZE_CONFLICT"), None)
    assert a is not None, "SAMPLE_SIZE_CONFLICT alert not raised"
    assert a["severity"] == "HIGH"
    assert "CP-2024-001" in a["sources"]
    assert "CSR-2024-001" in a["sources"]
    assert "40" in a["description"] or "38" in a["description"]

# ── Test 4: Alert 2 – Assay Version Mismatch ──────────────────────────────

def test_alert_assay_version_mismatch():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "ASSAY_VERSION_MISMATCH"), None)
    assert a is not None, "ASSAY_VERSION_MISMATCH alert not raised"
    assert a["severity"] == "HIGH"
    assert "SOP-AV-010" in a["sources"]
    desc_lower = a["description"].lower()
    assert "am-001" in desc_lower

# ── Test 5: Alert 3 – Outdated SOP Dependency ─────────────────────────────

def test_alert_outdated_sop_dependency():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "OUTDATED_SOP_DEPENDENCY"), None)
    assert a is not None, "OUTDATED_SOP_DEPENDENCY alert not raised"
    assert a["severity"] == "MEDIUM"
    assert "REG-001" in a["sources"]
    assert "SOP-302" in a["description"]

# ── Test 6: Alert 4 – Dose Safety Violation ───────────────────────────────

def test_alert_dose_safety_violation():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "DOSE_SAFETY_VIOLATION"), None)
    assert a is not None, "DOSE_SAFETY_VIOLATION alert not raised"
    assert a["severity"] == "CRITICAL"
    assert "TOX-PRE-003" in a["sources"]
    assert "CP-2024-001" in a["sources"]
    assert "1.5e11" in a["description"] or "1.5e12" in a["description"]

# ── Test 7: Alert 5 – NOAEL Trace Mismatch ────────────────────────────────

def test_alert_noael_trace_mismatch():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "NOAEL_TRACE_MISMATCH"), None)
    assert a is not None, "NOAEL_TRACE_MISMATCH alert not raised"
    assert a["severity"] == "CRITICAL"
    assert "TOX-SUM-001" in a["sources"]
    assert "IND-2024-MOD4" in a["sources"]
    assert "5.0e12" in a["description"] or "5.0e13" in a["description"]

# ── Test 8: Alert 6 – Vector Design Mismatch ──────────────────────────────

def test_alert_vector_design_mismatch():
    _, _, _, alerts = _full_pipeline()
    a = next((x for x in alerts if x["alert_type"] == "VECTOR_DESIGN_MISMATCH"), None)
    assert a is not None, "VECTOR_DESIGN_MISMATCH alert not raised"
    assert a["severity"] == "CRITICAL"
    desc = a["description"]
    assert "scAAV" in desc or "rAAV" in desc

# ── Test 9: Impact report totals ──────────────────────────────────────────

def test_impact_report_totals():
    _, _, _, alerts = _full_pipeline()
    report = generate_report(alerts)
    assert report["total_alerts"] == len(alerts)
    assert report["critical_count"] == sum(1 for a in alerts if a["severity"] == "CRITICAL")
    assert report["high_count"]     == sum(1 for a in alerts if a["severity"] == "HIGH")
    assert "report_id" in report
    assert "generated_at" in report
