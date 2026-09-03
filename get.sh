#!/bin/sh
set -e
D=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cp "$D/infill-tests.md" tests/test.patch
cp "$D/infill-solution.md" solution/solution.patch
wc -l tests/test.patch solution/solution.patch
