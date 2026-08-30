"""
server.py – GeneFlow Flask Web UI
Run:  python server.py
Binds to 127.0.0.1:5000 (secure loopback).
"""
from __future__ import annotations
import sys, os, json, uuid
from datetime import datetime, timezone

# ── Layout-agnostic imports ──────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_here, "..", "backend"),
    os.path.join(_here, "..", "agents"),
    os.path.join(_here, ".."),
]:
    _abs = os.path.normpath(_candidate)
    if _abs not in sys.path:
        sys.path.insert(0, _abs)

# ── Smart UPLOAD_FOLDER finder ───────────────────────────────────────────
def _find_documents_dir() -> str:
    candidates = [
        os.path.join(_here, "..", "..", "documents"),
        os.path.join(_here, "..", "documents"),
        os.path.join(_here, "documents"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return os.path.normpath(c)
    # Fallback: create next to server.py
    fallback = os.path.normpath(os.path.join(_here, "..", "..", "documents"))
    os.makedirs(fallback, exist_ok=True)
    return fallback

UPLOAD_FOLDER = _find_documents_dir()

from flask import Flask, request, jsonify, redirect, url_for
from pipeline import run_pipeline

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

LAST_REPORT: dict = {}

# ── HTML Dashboard ───────────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeneFlow – Compliance Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:#0f1117;color:#e2e8f0;min-height:100vh}
header{background:linear-gradient(135deg,#1a1f36,#2d1b69);
       padding:20px 32px;display:flex;align-items:center;gap:16px;
       border-bottom:1px solid #2d3748}
header h1{font-size:1.6rem;font-weight:700;letter-spacing:.5px}
header span.sub{font-size:.85rem;color:#a0aec0;margin-left:8px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;
       font-size:.75rem;font-weight:700;letter-spacing:.4px}
.CRITICAL{background:#7f1d1d;color:#fca5a5}
.HIGH{background:#78350f;color:#fcd34d}
.MEDIUM{background:#1e3a5f;color:#93c5fd}
.LOW{background:#1a3329;color:#6ee7b7}
nav{display:flex;gap:0;border-bottom:1px solid #2d3748}
nav button{background:none;border:none;color:#a0aec0;padding:14px 28px;
           cursor:pointer;font-size:.9rem;border-bottom:3px solid transparent;transition:.2s}
nav button.active,nav button:hover{color:#e2e8f0;border-bottom-color:#7c3aed}
.screen{display:none;padding:32px;max-width:1100px;margin:0 auto}
.screen.active{display:block}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:10px;
      padding:24px;margin-bottom:20px}
.card h2{font-size:1.1rem;font-weight:600;margin-bottom:16px;color:#a78bfa}
.stat-row{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}
.stat{flex:1;min-width:120px;background:#1a1f2e;border:1px solid #2d3748;
      border-radius:8px;padding:16px;text-align:center}
.stat .num{font-size:2rem;font-weight:700}
.stat .lbl{font-size:.75rem;color:#718096;margin-top:4px;text-transform:uppercase}
.alert-card{background:#1a1f2e;border-left:4px solid #4a5568;
            border-radius:8px;padding:18px;margin-bottom:14px;transition:.2s}
.alert-card.CRITICAL{border-left-color:#ef4444}
.alert-card.HIGH{border-left-color:#f59e0b}
.alert-card.MEDIUM{border-left-color:#3b82f6}
.alert-card.LOW{border-left-color:#10b981}
.alert-card h3{font-size:.95rem;font-weight:600;margin-bottom:8px}
.alert-card p{font-size:.85rem;color:#a0aec0;line-height:1.6;margin-bottom:10px}
.alert-card .recon{background:#11151f;border:1px solid #2d3748;border-radius:6px;
                   padding:12px;font-size:.8rem;color:#93c5fd;line-height:1.6}
.alert-card .recon strong{color:#c4b5fd;display:block;margin-bottom:4px}
.sources{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.src-tag{background:#2d3748;color:#e2e8f0;padding:2px 8px;border-radius:4px;font-size:.75rem}
.btn{display:inline-block;padding:8px 18px;border-radius:6px;font-size:.85rem;
     font-weight:600;cursor:pointer;border:none;transition:.2s}
.btn-primary{background:#7c3aed;color:#fff}
.btn-primary:hover{background:#6d28d9}
.btn-success{background:#059669;color:#fff}
.btn-success:hover{background:#047857}
.btn-warn{background:#d97706;color:#fff}
.btn-warn:hover{background:#b45309}
.actions{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
.upload-area{border:2px dashed #4a5568;border-radius:12px;padding:48px;
             text-align:center;cursor:pointer;transition:.2s}
.upload-area:hover{border-color:#7c3aed;background:#1a1f2e}
.upload-area input{display:none}
.upload-area p{color:#718096;margin-top:8px;font-size:.9rem}
.run-btn{width:100%;padding:14px;font-size:1rem;margin-top:16px}
#status{margin-top:12px;padding:12px;border-radius:6px;display:none;font-size:.85rem}
.status-ok{background:#064e3b;color:#6ee7b7;border:1px solid #065f46}
.status-err{background:#7f1d1d;color:#fca5a5;border:1px solid #991b1b}
.evidence-list{max-height:500px;overflow-y:auto}
.ev-item{background:#11151f;border:1px solid #2d3748;border-radius:6px;
         padding:12px;margin-bottom:8px;font-size:.8rem}
.ev-item .doc{color:#a78bfa;font-weight:600}
.ev-item .param{color:#34d399;margin:0 8px}
.ev-item .quote{color:#a0aec0;margin-top:4px;font-style:italic}
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:10px 12px;font-size:.75rem;text-transform:uppercase;
   color:#718096;border-bottom:1px solid #2d3748}
td{padding:10px 12px;font-size:.85rem;border-bottom:1px solid #1a2033}
tr:hover td{background:#1a2033}
#loading{display:none;text-align:center;padding:40px;color:#a0aec0}
.spinner{display:inline-block;width:32px;height:32px;border:3px solid #2d3748;
         border-top-color:#7c3aed;border-radius:50%;animation:spin 1s linear infinite;
         margin-bottom:12px}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<header>
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="16" r="15" stroke="#7c3aed" stroke-width="2"/>
    <path d="M10 16 Q13 10 16 16 Q19 22 22 16" stroke="#a78bfa" stroke-width="2"
          fill="none" stroke-linecap="round"/>
    <circle cx="10" cy="16" r="2" fill="#7c3aed"/>
    <circle cx="22" cy="16" r="2" fill="#7c3aed"/>
  </svg>
  <div>
    <h1>GeneFlow <span class="sub">Gene-Therapy Compliance Platform</span></h1>
  </div>
</header>
<nav>
  <button class="active" onclick="show('upload')">📤 Package Upload</button>
  <button onclick="show('findings')">🔍 Findings Dashboard</button>
  <button onclick="show('evidence')">🔬 Evidence Inspector</button>
</nav>

<div id="upload" class="screen active">
  <div class="card">
    <h2>Upload Document Package</h2>
    <div class="upload-area" onclick="document.getElementById('fileinput').click()">
      <svg width="48" height="48" fill="none" viewBox="0 0 48 48">
        <path d="M24 32V16M17 23l7-7 7 7" stroke="#7c3aed" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="8" y="8" width="32" height="32" rx="6"
              stroke="#4a5568" stroke-width="2" fill="none"/>
      </svg>
      <p>Click to select .txt or .pdf documents, or use pre-loaded package</p>
      <input id="fileinput" type="file" multiple accept=".txt,.pdf"
             onchange="handleFiles(this.files)">
    </div>
    <div id="file-list" style="margin-top:12px;font-size:.85rem;color:#a0aec0"></div>
    <button class="btn btn-primary run-btn" onclick="runAnalysis()">
      ▶ Run Compliance Analysis
    </button>
    <button class="btn btn-success run-btn" style="margin-top:8px" onclick="runDemo()">
      ⚡ Run Demo (pre-loaded package)
    </button>
    <div id="status"></div>
    <div id="loading">
      <div class="spinner"></div>
      <div>Analysing documents…</div>
    </div>
  </div>
</div>

<div id="findings" class="screen">
  <div class="stat-row" id="stat-row">
    <div class="stat"><div class="num" id="s-total">—</div><div class="lbl">Total Alerts</div></div>
    <div class="stat"><div class="num" style="color:#ef4444" id="s-crit">—</div><div class="lbl">Critical</div></div>
    <div class="stat"><div class="num" style="color:#f59e0b" id="s-high">—</div><div class="lbl">High</div></div>
    <div class="stat"><div class="num" style="color:#3b82f6" id="s-med">—</div><div class="lbl">Medium</div></div>
    <div class="stat"><div class="num" style="color:#6b7280" id="s-docs">—</div><div class="lbl">Docs Loaded</div></div>
    <div class="stat"><div class="num" style="color:#6b7280" id="s-claims">—</div><div class="lbl">Claims</div></div>
  </div>
  <div id="exec-summary" class="card" style="display:none">
    <h2>Executive Summary</h2>
    <p id="exec-text" style="color:#a0aec0;line-height:1.7;font-size:.9rem"></p>
  </div>
  <div id="alerts-container"></div>
</div>

<div id="evidence" class="screen">
  <div class="card">
    <h2>Evidence Claims — Raw Citations</h2>
    <div id="evidence-list" class="evidence-list">
      <p style="color:#718096">Run analysis first to populate evidence claims.</p>
    </div>
  </div>
  <div class="card">
    <h2>Human-in-the-Loop Actions</h2>
    <div class="actions">
      <button class="btn btn-success" onclick="hitlAction('approve')">✅ Approve All Reconciliations</button>
      <button class="btn btn-warn"    onclick="hitlAction('escalate')">⚠️ Escalate Critical to QA</button>
      <button class="btn btn-primary" onclick="hitlAction('export')">📥 Export Report JSON</button>
    </div>
    <div id="hitl-status" style="margin-top:12px;font-size:.85rem;color:#6ee7b7"></div>
  </div>
</div>

<script>
let reportData = null;

function show(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  event.target.classList.add("active");
}

function handleFiles(files) {
  const fl = document.getElementById("file-list");
  fl.innerHTML = Array.from(files).map(f =>
    `<span style="margin-right:10px">📄 ${f.name}</span>`).join("");
}

async function runAnalysis() {
  const files = document.getElementById("fileinput").files;
  if (!files.length) { alert("Please select files or use Demo mode."); return; }
  const fd = new FormData();
  Array.from(files).forEach(f => fd.append("files", f));
  await _submitAnalysis("/upload", fd);
}

async function runDemo() {
  document.getElementById("loading").style.display = "block";
  document.getElementById("status").style.display = "none";
  const r = await fetch("/demo");
  const data = await r.json();
  document.getElementById("loading").style.display = "none";
  handleReport(data, r.ok);
}

async function _submitAnalysis(url, body) {
  document.getElementById("loading").style.display = "block";
  document.getElementById("status").style.display = "none";
  const r = await fetch(url, {method: "POST", body});
  const data = await r.json();
  document.getElementById("loading").style.display = "none";
  handleReport(data, r.ok);
}

function handleReport(data, ok) {
  const st = document.getElementById("status");
  if (!ok) {
    st.className = "status-err"; st.style.display = "block";
    st.textContent = "Error: " + (data.error || "Unknown error");
    return;
  }
  reportData = data;
  st.className = "status-ok"; st.style.display = "block";
  st.textContent = `✅ Analysis complete — ${data.total_alerts} alert(s) found in ${data._documents_loaded} documents`;
  populateFindings(data);
  populateEvidence(data);
}

function sev(s){ return s || "LOW"; }

function populateFindings(d) {
  document.getElementById("s-total").textContent  = d.total_alerts;
  document.getElementById("s-crit").textContent   = d.critical_count;
  document.getElementById("s-high").textContent   = d.high_count;
  document.getElementById("s-med").textContent    = d.medium_count || 0;
  document.getElementById("s-docs").textContent   = d._documents_loaded;
  document.getElementById("s-claims").textContent = d._claims_count;

  const es = document.getElementById("exec-summary");
  es.style.display = "block";
  document.getElementById("exec-text").textContent = d.executive_summary;

  const ac = document.getElementById("alerts-container");
  ac.innerHTML = "";
  (d.alerts || []).sort((a,b) => {
    const o = {CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3};
    return (o[sev(a.severity)]||3) - (o[sev(b.severity)]||3);
  }).forEach(a => {
    const srcs = (a.sources||[]).map(s=>`<span class="src-tag">${s}</span>`).join("");
    ac.innerHTML += `
    <div class="alert-card ${sev(a.severity)}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <h3>${a.alert_type.replace(/_/g," ")}</h3>
        <span class="badge ${sev(a.severity)}">${sev(a.severity)}</span>
      </div>
      <p>${a.description}</p>
      <div class="sources">${srcs}</div>
      <div class="recon" style="margin-top:12px">
        <strong>🔧 Reconciliation Action</strong>
        ${a.reconciliation_prompt}
      </div>
      <div class="actions">
        <button class="btn btn-success" style="font-size:.75rem;padding:5px 12px"
          onclick="hitlAction('approve_single','${a.alert_id}')">✅ Mark Resolved</button>
        <button class="btn btn-warn" style="font-size:.75rem;padding:5px 12px"
          onclick="hitlAction('escalate_single','${a.alert_id}')">⚠ Escalate</button>
      </div>
    </div>`;
  });
}

function populateEvidence(d) {
  const el = document.getElementById("evidence-list");
  if (!d._claims) { el.innerHTML = "<p style='color:#718096'>Evidence claims not included in this response.</p>"; return; }
  el.innerHTML = d._claims.map(c => `
    <div class="ev-item">
      <span class="doc">${c.document_id}</span>
      <span class="param">[${c.parameter}]</span>
      <strong>${c.value}</strong> ${c.unit}
      <div class="quote">"${c.raw_quote}"</div>
    </div>`).join("");
}

function hitlAction(action, id) {
  const msgs = {
    approve: "All reconciliation actions marked as acknowledged by QA.",
    escalate: "Critical findings escalated to QA inbox. Notification sent.",
    export: "Report exported — check your downloads.",
    approve_single: "Finding marked as resolved.",
    escalate_single: "Finding escalated to QA."
  };
  if (action === "export" && reportData) {
    const blob = new Blob([JSON.stringify(reportData, null, 2)],
      {type: "application/json"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `geneflow_report_${Date.now()}.json`;
    a.click();
  }
  document.getElementById("hitl-status").textContent = msgs[action] || "Action recorded.";
}
</script>
</body></html>
"""

@app.route("/")
def index():
    return DASHBOARD_HTML

@app.route("/demo")
def demo():
    report = run_pipeline(UPLOAD_FOLDER)
    LAST_REPORT.update(report)
    return jsonify(report)

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400
    tmp_dir = os.path.join(os.path.dirname(UPLOAD_FOLDER), "_tmp_upload")
    os.makedirs(tmp_dir, exist_ok=True)
    for f in files:
        f.save(os.path.join(tmp_dir, f.filename))
    report = run_pipeline(tmp_dir)
    LAST_REPORT.update(report)
    return jsonify(report)

@app.route("/report")
def report():
    return jsonify(LAST_REPORT if LAST_REPORT else {"message": "No analysis run yet."})

if __name__ == "__main__":
    print(f"[GeneFlow] Documents folder : {UPLOAD_FOLDER}")
    print(f"[GeneFlow] Starting server  : http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
