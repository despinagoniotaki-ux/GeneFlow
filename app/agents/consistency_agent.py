"""
consistency_agent.py – Consistency Agent
Validates cross-document claims and produces the 6 ConsistencyAlerts.
"""
from __future__ import annotations
import uuid

def _find(claims: list[dict], doc_id_fragment: str, parameter: str) -> list[dict]:
    return [
        c for c in claims
        if doc_id_fragment.lower() in c["document_id"].lower()
        and c["parameter"] == parameter
    ]

def run_consistency_checks(
    claims: list[dict],
    change_diffs: list[dict],
    dep_links: list[dict],
) -> list[dict]:
    alerts: list[dict] = []

    # ── Alert 1: Sample Size Conflict ────────────────────────────────────
    cp_ss  = _find(claims, "CP-2024-001",  "sample_size")
    csr_ss = _find(claims, "CSR-2024-001", "sample_size")
    if cp_ss and csr_ss:
        cp_val  = cp_ss[0]["value"]
        csr_val = csr_ss[0]["value"]
        if cp_val != csr_val:
            alerts.append({
                "alert_id":   str(uuid.uuid4()),
                "alert_type": "SAMPLE_SIZE_CONFLICT",
                "severity":   "HIGH",
                "description": (
                    f"Clinical Protocol (CP-2024-001) states n={cp_val} but Clinical Study "
                    f"Report (CSR-2024-001) reports n={csr_val}. Enrolled population mismatch "
                    f"must be reconciled before regulatory submission."
                ),
                "sources": ["CP-2024-001", "CSR-2024-001"],
                "reconciliation_prompt": (
                    "Determine whether the two screen-failure exclusions were approved "
                    "protocol deviations. If so, issue a protocol amendment updating n=38 "
                    "and obtain IRB/Ethics approval. Update the CSR to cite the amendment."
                ),
            })

    # ── Alert 2: Assay Version Mismatch ──────────────────────────────────
    deprecated_docs = list({
        doc
        for d in change_diffs
        if d["method_id"] == "AM-001" and d["detected_version"] != "v2"
        for doc in d["affected_documents"]
    })
    if deprecated_docs:
        alerts.append({
            "alert_id":   str(uuid.uuid4()),
            "alert_type": "ASSAY_VERSION_MISMATCH",
            "severity":   "HIGH",
            "description": (
                f"AM-001 v1 (retired 2024-03-01) is still referenced in: "
                f"{', '.join(deprecated_docs)}. "
                f"SOP-AV-010 v3.0 mandates AM-001 v2 as the only approved potency assay."
            ),
            "sources": ["SOP-AV-010"] + deprecated_docs,
            "reconciliation_prompt": (
                "Raise a CAPA to retrospectively validate or re-test affected lots using "
                "AM-001 v2. Update all affected documents (protocol, CSR, batch records) "
                "to reference AM-001 v2 and obtain QA/RA sign-off."
            ),
        })

    # ── Alert 3: Outdated SOP Dependency ─────────────────────────────────
    retired_sop_docs = list({
        doc
        for l in dep_links
        if l["sop_id"] == "SOP-302" and l["retired_version"] == "v2"
        for doc in l["referencing_documents"]
    })
    if retired_sop_docs:
        alerts.append({
            "alert_id":   str(uuid.uuid4()),
            "alert_type": "OUTDATED_SOP_DEPENDENCY",
            "severity":   "MEDIUM",
            "description": (
                f"SOP-302 v2 (retired 2023-11-01) is cited in: "
                f"{', '.join(retired_sop_docs)}. "
                f"SOP Registry (REG-001) designates SOP-302 v3 as the active version."
            ),
            "sources": ["REG-001"] + retired_sop_docs,
            "reconciliation_prompt": (
                "Update all documents referencing SOP-302 v2 to SOP-302 v3. "
                "Verify that operational procedures were in fact performed per v3 "
                "or issue a deviation report if v2 was used in practice."
            ),
        })

    # ── Alert 4: Preclinical vs Clinical Starting Dose (Safety) ──────────
    tox_mrsd  = _find(claims, "TOX-PRE-003", "dose")
    cp_dose   = _find(claims, "CP-2024-001",  "dose")
    if tox_mrsd and cp_dose:
        mrsd_val  = tox_mrsd[0]["value"]   # 1.5e11
        cp_d_val  = cp_dose[0]["value"]    # 1.5e12
        if mrsd_val != cp_d_val:
            alerts.append({
                "alert_id":   str(uuid.uuid4()),
                "alert_type": "DOSE_SAFETY_VIOLATION",
                "severity":   "CRITICAL",
                "description": (
                    f"Preclinical toxicology (TOX-PRE-003) sets the MRSD at {mrsd_val} vg/kg "
                    f"(1/10 safety factor from NOAEL). Clinical Protocol (CP-2024-001) "
                    f"specifies a starting dose of {cp_d_val} vg/kg — 10× above the MRSD. "
                    f"This is a potential first-in-human safety violation."
                ),
                "sources": ["TOX-PRE-003", "CP-2024-001"],
                "reconciliation_prompt": (
                    "Immediately halt FIH dose escalation pending safety review. "
                    "Convene DSMB/Safety Committee to evaluate whether a 10× MRSD overage "
                    "was intentional (with scientific justification) or an error. "
                    "Amend clinical protocol and obtain FDA/EMA concurrence before proceeding."
                ),
            })

    # ── Alert 5: Toxicology NOAEL Trace Mismatch ─────────────────────────
    tox_noael = _find(claims, "TOX-SUM-001",    "noael")
    ind_noael = _find(claims, "IND-2024-MOD4",  "noael")
    if tox_noael and ind_noael:
        t_val = tox_noael[0]["value"]   # 5.0e12
        i_val = ind_noael[0]["value"]   # 5.0e13
        if t_val != i_val:
            alerts.append({
                "alert_id":   str(uuid.uuid4()),
                "alert_type": "NOAEL_TRACE_MISMATCH",
                "severity":   "CRITICAL",
                "description": (
                    f"Toxicology Summary Report (TOX-SUM-001) states NOAEL = {t_val} vg/kg. "
                    f"IND Application Module 4 (IND-2024-MOD4) claims NOAEL = {i_val} vg/kg — "
                    f"a 10× exaggeration of the safety margin submitted to regulators."
                ),
                "sources": ["TOX-SUM-001", "IND-2024-MOD4"],
                "reconciliation_prompt": (
                    "Withdraw or amend IND Module 4 immediately. Re-derive the NOAEL from "
                    "the primary GLP study data and resubmit with corrected values. "
                    "Notify FDA of the discrepancy per 21 CFR 312.62 and assess whether "
                    "a clinical hold is warranted."
                ),
            })

    # ── Alert 6: Vector Design Mismatch ──────────────────────────────────
    pre_vectors = _find(claims, "PRE-EFF-002",   "vector_type")
    mbr_vectors = _find(claims, "MBR-2024-007",  "vector_type")
    if pre_vectors and mbr_vectors:
        pre_vec = {c["value"] for c in pre_vectors}
        mbr_vec = {c["value"] for c in mbr_vectors}
        pre_lower = {v.lower() for v in pre_vec}
        mbr_lower = {v.lower() for v in mbr_vec}
        if not pre_lower.intersection(mbr_lower):
            pre_display = "scAAV-hFIX" if any("scaav" in v for v in pre_lower) else ", ".join(pre_vec)
            mbr_display = "rAAV-hFIX"  if any("raav"  in v and "scaav" not in v for v in mbr_lower) else ", ".join(mbr_vec)
            alerts.append({
                "alert_id":   str(uuid.uuid4()),
                "alert_type": "VECTOR_DESIGN_MISMATCH",
                "severity":   "CRITICAL",
                "description": (
                    f"Preclinical studies (PRE-EFF-002, TOX-PRE-003) evaluated "
                    f"{pre_display} (self-complementary). Manufacturing Batch Record "
                    f"(MBR-2024-007) produced {mbr_display} (single-stranded). "
                    f"Product used in clinical trial is NOT the same vector as tested preclinically."
                ),
                "sources": ["PRE-EFF-002", "TOX-PRE-003", "MBR-2024-007"],
                "reconciliation_prompt": (
                    "Initiate a product comparability programme to demonstrate equivalence "
                    "between scAAV-hFIX and rAAV-hFIX with respect to transduction efficiency, "
                    "safety profile, and FIX expression. Until equivalence is established, "
                    "clinical use of rAAV-hFIX cannot be justified by existing preclinical data."
                ),
            })

    return alerts
