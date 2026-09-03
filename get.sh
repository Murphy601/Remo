#!/bin/sh
set -e
D=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

ROOT=""
for cand in . /workspace "$HOME" /task /eval /app /data /home/workspace; do
  if [ -f "$cand/task.toml" ] || [ -f "$cand/tests/grader.py" ]; then
    ROOT=$cand
    break
  fi
done

if [ -z "$ROOT" ]; then
  found=$(find . /workspace /home /task /eval -maxdepth 5 -name task.toml 2>/dev/null | head -1)
  if [ -n "$found" ]; then
    ROOT=$(dirname "$found")
  fi
fi

if [ -z "$ROOT" ]; then
  ROOT=.
fi

mkdir -p "$ROOT/tests" "$ROOT/solution"
cp "$D/infill-tests.md" "$ROOT/tests/test.patch"
cp "$D/infill-solution.md" "$ROOT/solution/solution.patch"
if [ -f "$D/instruction.md" ]; then
  cp "$D/instruction.md" "$ROOT/instruction.md"
fi
if [ -f "$D/config.json" ]; then
  cp "$D/config.json" "$ROOT/tests/config.json"
fi

echo "root=$ROOT"
wc -l "$ROOT/tests/test.patch" "$ROOT/solution/solution.patch"
