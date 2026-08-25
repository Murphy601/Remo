#!/usr/bin/env python3
"""LibreOffice page counts for documents/*.docx."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = ROOT / "documents"
OUT_JSON = ROOT / "catalog" / "page_counts.json"


def pdfinfo_pages(pdf: Path) -> int:
    p = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in p.stdout.splitlines():
        if line.lower().startswith("pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"no Pages: in pdfinfo for {pdf}")


def convert_one(docx: Path, pdf_dir: Path) -> tuple[str, int]:
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_dir),
            str(docx),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf = pdf_dir / (docx.stem + ".pdf")
    pages = pdfinfo_pages(pdf)
    pdf.unlink(missing_ok=True)
    return docx.stem, pages


def main() -> int:
    files = sorted(DOC_DIR.glob("*.docx"))
    if not files:
        print("no docx", file=sys.stderr)
        return 1
    pdf_dir = Path("/tmp/remo-pdf")
    if pdf_dir.exists():
        shutil.rmtree(pdf_dir)
    pdf_dir.mkdir(parents=True)
    workers = min(4, os.cpu_count() or 2)
    counts = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(convert_one, f, pdf_dir) for f in files]
        for fut in as_completed(futs):
            stem, pages = fut.result()
            counts[stem] = pages
            flag = "OK" if 40 <= pages <= 50 else "OUT"
            print(f"{flag:3} {pages:3d}p  {stem}")
    ordered = {k: counts[k] for k in sorted(counts)}
    OUT_JSON.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
    vals = list(ordered.values())
    print(
        f"\n{len(vals)} files  min={min(vals)}  max={max(vals)}  "
        f"in_40_50={sum(1 for v in vals if 40 <= v <= 50)}"
    )
    return 0 if all(40 <= v <= 50 for v in vals) else 2


if __name__ == "__main__":
    sys.exit(main())
