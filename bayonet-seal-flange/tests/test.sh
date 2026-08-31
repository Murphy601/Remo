#!/bin/bash
set -u

mkdir -p /logs/verifier
chown root:root /logs/verifier 2>/dev/null || true
chmod 700 /logs/verifier
if [ -d /tests ]; then
    chown root:root /tests 2>/dev/null || true
    chmod 700 /tests
    find /tests -type d -exec chmod 700 {} \;
    find /tests -type f -exec chmod 600 {} \;
    chmod 700 /tests/test.sh 2>/dev/null || true
fi

reward() {
    echo "$1" > /logs/verifier/reward.txt
    chmod 600 /logs/verifier/reward.txt 2>/dev/null || true
}

reward 0
trap 'if [ ! -f /logs/verifier/reward.txt ]; then reward 0; fi' EXIT

python3 -m pytest /tests/test_outputs.py -q --ctrf /logs/verifier/ctrf.json
rc=$?
if [ "$rc" -eq 0 ]; then
    reward 1
else
    reward 0
fi

chmod 755 /logs/verifier 2>/dev/null || true
chmod 644 /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true
exit 0
