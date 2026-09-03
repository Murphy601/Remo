#!/bin/sh
set -e
D=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

echo "pwd=$PWD"
echo "source=$D"

ROOT=""
for cand in . /workspace "$HOME" /task /eval /app /data /home/workspace /home/ubuntu; do
  if [ -f "$cand/task.toml" ] || [ -f "$cand/tests/grader.py" ]; then
    ROOT=$cand
    break
  fi
done

if [ -z "$ROOT" ]; then
  found=$(find . /workspace /home /task /eval /app /data /opt -maxdepth 6 \( -name task.toml -o -name grader.py \) 2>/dev/null | head -1)
  if [ -n "$found" ]; then
    case $found in
      */task.toml) ROOT=$(dirname "$found") ;;
      */grader.py) ROOT=$(dirname "$(dirname "$found")") ;;
      *) ROOT=. ;;
    esac
  fi
fi

if [ -z "$ROOT" ]; then
  ROOT=.
fi

echo "root=$ROOT"
ls -la "$ROOT" | sed -n '1,20p'

mkdir -p "$ROOT/tests" "$ROOT/solution"
cp "$D/infill-tests.md" "$ROOT/tests/test.patch"
cp "$D/infill-solution.md" "$ROOT/solution/solution.patch"
cp "$D/instruction.md" "$ROOT/instruction.md"
cp "$D/config.json" "$ROOT/tests/config.json"

wc -l "$ROOT/tests/test.patch" "$ROOT/solution/solution.patch"
ls -l "$ROOT/tests/test.patch" "$ROOT/solution/solution.patch"
