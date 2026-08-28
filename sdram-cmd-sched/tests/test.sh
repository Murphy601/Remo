#!/bin/bash
set -u

OUT=/logs/verifier
BUILD=/tmp/mc_build
mkdir -p "$OUT" "$BUILD"
chown root:root "$OUT" 2>/dev/null || true
chmod 700 "$OUT"
if [ -d /tests ]; then
    chown root:root /tests
    chmod 700 /tests
    find /tests -type d -exec chmod 700 {} \;
    find /tests -type f -exec chmod 600 {} \;
    chmod 700 /tests/test.sh 2>/dev/null || true
fi

mark() {
    echo "$1" > "$OUT/reward.txt"
    chmod 600 "$OUT/reward.txt" 2>/dev/null || true
}

trap 'if [ ! -f '"$OUT"'/reward.txt ]; then mark 0; fi' EXIT

python3 -m pytest /tests/test_mc.py -q --ctrf "$OUT/ctrf.json"
if [ "$?" -eq 0 ]; then
    mark 1
else
    mark 0
fi
chmod 755 "$OUT" 2>/dev/null || true
chmod 644 "$OUT/reward.txt" "$OUT/ctrf.json" 2>/dev/null || true
exit 0
