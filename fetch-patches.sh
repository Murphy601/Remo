#!/bin/sh
set -e
curl -L -o tests/test.patch https://raw.githubusercontent.com/Murphy601/Remo/cursor/holiday-infill-lines-32c6/infill-tests.md
curl -L -o solution/solution.patch https://raw.githubusercontent.com/Murphy601/Remo/cursor/holiday-infill-lines-32c6/infill-solution.md
wc -l tests/test.patch solution/solution.patch
