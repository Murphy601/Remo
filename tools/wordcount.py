#!/usr/bin/env python3
"""Count words in a catalog document JSON (summary + all block text/items/cells)."""
import json
import re
import sys
from pathlib import Path


def tokenize(s: str) -> int:
    if not s:
        return 0
    return len(re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)?", s))


def count_block(b: dict) -> int:
    n = 0
    for key in ("text", "caption", "label"):
        n += tokenize(b.get(key, "") or "")
    items = b.get("items")
    if isinstance(items, list):
        for it in items:
            n += tokenize(str(it))
    headers = b.get("headers")
    if isinstance(headers, list):
        for h in headers:
            n += tokenize(str(h))
    rows = b.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, list):
                for cell in row:
                    n += tokenize(str(cell))
            else:
                n += tokenize(str(row))
    return n


def count_doc(path: Path) -> dict:
    doc = json.loads(path.read_text())
    n = tokenize(doc.get("summary", ""))
    for b in doc.get("blocks", []):
        n += count_block(b)
    return {
        "slug": doc.get("slug"),
        "path": str(path),
        "words": n,
        "blocks": len(doc.get("blocks", [])),
        "ok_json": True,
    }


def main():
    paths = sys.argv[1:] or sorted(Path("/workspace/content").glob("*.json"))
    for p in paths:
        info = count_doc(Path(p))
        flag = "OK" if info["words"] >= 2800 else "SHORT"
        print(f"{info['words']:5d}  {flag:5s}  {info['blocks']:3d} blocks  {Path(p).name}")


if __name__ == "__main__":
    main()
