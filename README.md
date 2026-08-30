# GeneFlow – Gene-Therapy Compliance MVP

## Quick Start

```bash
cd ~/Downloads/GeneFlow_MVP
pip install flask pytest
# Run the web UI
python app/frontend/server.py
# Open http://127.0.0.1:5000 → click "Run Demo"
# Run tests
pytest tests/ -v
```

## Architecture
```
GeneFlow_MVP/
├── app/
│   ├── backend/
│   │   ├── ingest.py           # Document ingestor
│   │   └── pipeline.py         # Orchestrator
│   ├── agents/
│   │   ├── evidence_extractor.py
│   │   ├── change_detector.py
│   │   ├── dependency_agent.py
│   │   ├── consistency_agent.py
│   │   └── impact_report_agent.py
│   └── frontend/
│       └── server.py           # Flask dashboard (127.0.0.1:5000)
├── documents/                  # 10 mock compliance documents
├── schemas/                    # JSON schemas
├── tests/
│   └── test_agents.py          # 9 pytest tests
└── requirements.txt
```

## Planted Inconsistencies (6 findings)
| # | Type | Severity |
|---|------|----------|
| 1 | Sample Size Conflict (n=40 vs n=38) | HIGH |
| 2 | Assay Version Mismatch (AM-001 v1 vs v2) | HIGH |
| 3 | Outdated SOP Dependency (SOP-302 v2 vs v3) | MEDIUM |
| 4 | Dose Safety Violation (1.5e12 vs MRSD 1.5e11 vg/kg) | CRITICAL |
| 5 | NOAEL Trace Mismatch (5.0e12 vs 5.0e13 vg/kg in IND) | CRITICAL |
| 6 | Vector Design Mismatch (scAAV preclinical vs rAAV clinical) | CRITICAL |
