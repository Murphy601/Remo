#!/usr/bin/env python3
"""Scan generated docx XML plus content JSON for leftover flags."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BANNED = re.compile(
    r"handshake|furthermore|moreover|additionally|\bleverage\b|\butilize\b|"
    r"\brobust\b|seamless|holistic|\blandscape\b|\bdelve\b|cutting-edge|"
    r"\bempower\b|streamline|it's important to note|in order to|"
    r"at the end of the day|moving forward|\bsynergy\b|\bparadigm\b|"
    r"\bunlock\b|comprehensive|\bensure\b|facilitate|\bpivotal\b|"
    r"\bnestled\b|\btapestry\b|Cummins|Infosys|\bWipro\b|\bHCL\b|"
    r"Aman Kumar|Priya Nair|Oakridge|Riverview Health|Clearhaven|"
    r"ForgeNet|python-docx|Northstar Engineering",
    re.I,
)
EMDASH = re.compile(r"—")
EXAMPLE_HOST = re.compile(r"[a-z0-9.-]+\.example\b", re.I)


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    return re.sub(r"<[^>]+>", " ", xml)


def main() -> int:
    hits = []
    files = sorted((ROOT / "documents").glob("*.docx"))
    if not files:
        print("no docx", file=sys.stderr)
        return 1
    for path in files:
        text = docx_text(path)
        for rx, name in (
            (BANNED, "banned"),
            (EMDASH, "emdash"),
            (EXAMPLE_HOST, "example-host"),
        ):
            for m in rx.finditer(text):
                snippet = text[max(0, m.start() - 40) : m.end() + 40]
                snippet = re.sub(r"\s+", " ", snippet)
                hits.append(f"{path.name}  {name}  {m.group(0)!r}  …{snippet}…")
    if hits:
        print("\n".join(hits[:200]))
        print(f"\n{len(hits)} hits", file=sys.stderr)
        return 2
    print(f"OK  {len(files)} files, no banned/emdash/.example hits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
