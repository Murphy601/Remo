#!/usr/bin/env python3
"""LibreOffice page counts for documents/*.docx."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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


def convert_batch(files: list[Path], pdf_dir: Path) -> None:
    cmd = [
        "soffice",
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pdf_dir),
    ] + [str(f) for f in files]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.stderr.write(proc.stdout)
        raise RuntimeError(f"soffice failed: {proc.returncode}")


def main() -> int:
    files = sorted(DOC_DIR.glob("*.docx"))
    if not files:
        print("no docx", file=sys.stderr)
        return 1
    pdf_dir = Path("/tmp/remo-pdf")
    if pdf_dir.exists():
        shutil.rmtree(pdf_dir)
    pdf_dir.mkdir(parents=True)
    # One soffice process at a time. Concurrent profiles collide.
    batch = 8
    for i in range(0, len(files), batch):
        chunk = files[i : i + batch]
        convert_batch(chunk, pdf_dir)
        print(f"converted {i + len(chunk)}/{len(files)}", flush=True)
    counts = {}
    for docx in files:
        pdf = pdf_dir / (docx.stem + ".pdf")
        pages = pdfinfo_pages(pdf)
        counts[docx.stem] = pages
        flag = "OK" if 40 <= pages <= 50 else "OUT"
        print(f"{flag:3} {pages:3d}p  {docx.stem}")
        pdf.unlink(missing_ok=True)
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
