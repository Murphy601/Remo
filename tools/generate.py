#!/usr/bin/env python3
"""Render catalog JSON files into styled .docx documents."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from docx_builder import build_document, stamp_docx_metadata  # noqa: E402
from expand import expand_spec  # noqa: E402


def word_count(spec: dict) -> int:
    chunks = []
    for key in ("title", "subtitle", "summary", "team", "audience"):
        if spec.get(key):
            chunks.append(str(spec[key]))
    for row in spec.get("revision_history", []):
        chunks.extend(str(x) for x in row)
    for block in spec.get("blocks", []):
        if "text" in block:
            chunks.append(block["text"])
        if "items" in block:
            chunks.extend(block["items"])
        if "headers" in block:
            chunks.extend(block["headers"])
        if "rows" in block:
            for row in block["rows"]:
                chunks.extend(str(c) for c in row)
        if "caption" in block:
            chunks.append(block["caption"])
        if "label" in block:
            chunks.append(block["label"])
    text = " ".join(chunks)
    return len(re.findall(r"[A-Za-z0-9']+", text))


def main():
    content_dir = ROOT / "content"
    out_dir = ROOT / "documents"
    files = sorted(content_dir.glob("*.json"))
    if not files:
        print("No JSON files in content/", file=sys.stderr)
        sys.exit(1)

    page_baseline = {}
    pb = ROOT / "catalog" / "page_baseline.json"
    if pb.exists():
        page_baseline = json.loads(pb.read_text(encoding="utf-8"))

    catalog = []
    for path in files:
        spec = json.loads(path.read_text(encoding="utf-8"))
        slug = spec.get("slug") or path.stem
        spec = expand_spec(spec, min_words=14200, max_words=15400)
        out = out_dir / f"{slug}.docx"
        build_document(spec, out)
        wc = word_count(spec)
        # 12pt / 1.78 spacing historically ~310 words/page. 40-50 pages => ~12.4k-15.5k.
        est_pages = max(1, round(wc / 310))
        stamp_docx_metadata(out, spec, words=wc, pages=est_pages)
        rec = {
            "file": str(out.relative_to(ROOT)),
            "source": str(path.relative_to(ROOT)),
            "doc_id": spec.get("doc_id"),
            "title": spec.get("title"),
            "doc_type": spec.get("doc_type"),
            "date": spec.get("date"),
            "role": spec.get("role"),
            "words": wc,
            "est_pages": est_pages,
            "description": spec.get("form_description") or spec.get("summary", "")[:400],
            "field": spec.get("field", "Software Engineering / Data Science"),
        }
        catalog.append(rec)
        flag = "OK" if 12400 <= wc <= 15500 else "CHECK"
        print(f"{flag:5} {wc:5d}w  ~{est_pages:2d}p  {out.name}")

    (ROOT / "catalog" / "generated.json").write_text(
        json.dumps(catalog, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {len(catalog)} documents to {out_dir}")


if __name__ == "__main__":
    main()
