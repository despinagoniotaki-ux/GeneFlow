"""
ingest.py – Document Ingestor
Parses structured .txt files with header fields and named sections.
Also supports PDF extraction via PyMuPDF (fitz) when available.
"""
from __future__ import annotations
import os, re
from typing import Optional

def _try_pdf(path: str) -> Optional[str]:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    except Exception:
        return None

def load_document(path: str) -> dict:
    """Return a dict with metadata + list of {section, content} dicts."""
    _, ext = os.path.splitext(path)
    if ext.lower() == ".pdf":
        raw = _try_pdf(path)
        if raw is None:
            raise RuntimeError(f"Cannot parse PDF (PyMuPDF not installed): {path}")
    else:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()

    doc: dict = {"path": path, "metadata": {}, "sections": []}
    current_section: Optional[str] = None
    current_lines: list[str] = []

    header_fields = {"Document", "ID", "Version", "Date", "Author"}

    for line in raw.splitlines():
        # Top-level header key: value
        m = re.match(r"^(Document|ID|Version|Date|Author):\s*(.+)$", line)
        if m:
            doc["metadata"][m.group(1)] = m.group(2).strip()
            continue
        # Section header
        sm = re.match(r"^Section:\s*(.+)$", line)
        if sm:
            if current_section is not None:
                doc["sections"].append(
                    {"section": current_section,
                     "content": " ".join(current_lines).strip()}
                )
            current_section = sm.group(1).strip()
            current_lines = []
            continue
        # Content label (strip prefix)
        cl = re.match(r"^Content:\s*(.*)", line)
        if cl:
            rest = cl.group(1).strip()
            if rest:
                current_lines.append(rest)
            continue
        stripped = line.strip()
        if stripped and current_section:
            current_lines.append(stripped)

    if current_section is not None:
        doc["sections"].append(
            {"section": current_section,
             "content": " ".join(current_lines).strip()}
        )

    doc["full_text"] = raw
    return doc


def load_all(folder: str) -> list[dict]:
    docs = []
    for fname in sorted(os.listdir(folder)):
        fpath = os.path.join(folder, fname)
        if fname.endswith((".txt", ".pdf")):
            docs.append(load_document(fpath))
    return docs
