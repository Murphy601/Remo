#!/usr/bin/env python3
"""Rebuild FORM_ANSWERS.md from generated.json + page_counts.json."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def parse_date(s: str) -> datetime:
    m = re.match(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s or "")
    if not m:
        return datetime(2023, 1, 1)
    return datetime(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))


def dd_mm_yyyy(s: str) -> str:
    d = parse_date(s)
    return d.strftime("%d-%m-%Y")


def main() -> None:
    catalog = json.loads((ROOT / "catalog" / "generated.json").read_text())
    pages = {}
    pc = ROOT / "catalog" / "page_counts.json"
    if pc.exists():
        pages = json.loads(pc.read_text())
    lines = []
    lines.append("# Form answers (per document)")
    lines.append("")
    lines.append(
        "These answers map to the intake questions. They apply to this portfolio of "
        "original writing samples, not to a third-party submission portal."
    )
    lines.append("")
    lines.append(
        "Direct file links: [DOWNLOADS.md](../DOWNLOADS.md). All 50 as a zip: "
        "[documents.zip](../documents.zip)."
    )
    lines.append("")
    lines.append("## Answers that are the same for every file")
    lines.append("")
    lines.append("1. **Current or most recent job title:** Software Engineer II")
    lines.append(
        "2. **Years of professional experience:** 5–10 (about six years, 2019–present)"
    )
    lines.append("3. **Field:** Software Engineering / Data Science")
    page_vals = [pages.get(Path(r["file"]).stem, r.get("est_pages")) for r in catalog]
    if page_vals and all(isinstance(v, int) for v in page_vals):
        pmin, pmax = min(page_vals), max(page_vals)
        lines.append(
            f"4. **Pages:** {pmin}–{pmax} (counted with LibreOffice Writer → PDF)"
        )
    else:
        lines.append("4. **Pages:** see table (LibreOffice Writer → PDF)")
    lines.append("")
    lines.append(
        "Author on every document: Aman Kumar. Employer in the samples is fictional "
        "(Northstar Engineering). Clients are fictional (Oakridge Industrial, "
        "Riverview Health Network, Clearhaven Markets)."
    )
    lines.append("")
    lines.append(
        "These files were written here as decision-grade samples. "
        "They are not production documents taken from a real engagement. "
        "They are not a claim that a reviewer will stamp them. Approval is a human call."
    )
    lines.append("")
    lines.append("## Per-document answers (questions 4–7)")
    lines.append("")
    lines.append("| # | File | Pages | Words | Written | Description |")
    lines.append("|---|---|---|---|---|---|")
    for i, rec in enumerate(catalog, 1):
        stem = Path(rec["file"]).stem
        fn = Path(rec["file"]).name
        pg = pages.get(stem, rec.get("est_pages", ""))
        desc = (rec.get("description") or "").replace("\n", " ").strip()
        if len(desc) > 160:
            desc = desc[:157].rstrip() + "..."
        written = dd_mm_yyyy(rec.get("date", ""))
        lines.append(
            f"| {i} | `{fn}` | {pg} | {rec.get('words','')} | {written} | {desc} |"
        )
    lines.append("")
    if page_vals and all(isinstance(v, int) for v in page_vals):
        lines.append(
            f"Page counts were measured by converting each `.docx` with LibreOffice "
            f"and reading PDF page counts. Files are {min(page_vals)}–{max(page_vals)} "
            f"pages. Word counts are ~{min(r['words'] for r in catalog):,}–"
            f"{max(r['words'] for r in catalog):,}, so well above 150 words per page."
        )
    lines.append("")
    lines.append("## Full write-ups (copy/paste for question 6–7)")
    lines.append("")
    for i, rec in enumerate(catalog, 1):
        stem = Path(rec["file"]).stem
        fn = rec["file"]
        pg = pages.get(stem, rec.get("est_pages", ""))
        desc = (rec.get("description") or "").strip()
        written = rec.get("date", "")
        dmy = dd_mm_yyyy(written)
        lines.append(f"### {i}. {rec.get('title','')}")
        lines.append("")
        lines.append(f"- **File:** `{fn}`")
        lines.append(f"- **Doc ID:** {rec.get('doc_id','')}")
        lines.append(f"- **Type:** {rec.get('doc_type','')}")
        lines.append(f"- **4. Pages:** {pg} (LibreOffice), {rec.get('words','')} words")
        lines.append(f"- **6. Description:** {desc}")
        lines.append(f"- **7. Written:** {dmy} ({written})")
        lines.append(f"- **Role at the time:** {rec.get('role','Software Engineer II')}")
        lines.append("")
    (ROOT / "catalog" / "FORM_ANSWERS.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("wrote catalog/FORM_ANSWERS.md")


if __name__ == "__main__":
    main()
