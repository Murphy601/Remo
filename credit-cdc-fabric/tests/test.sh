#!/bin/bash
set -u

mkdir -p /logs/verifier /tmp/cdc_build
chown root:root /logs/verifier 2>/dev/null || true
chmod 700 /logs/verifier
if [ -d /tests ]; then
    chown root:root /tests
    chmod 700 /tests
    find /tests -type d -exec chmod 700 {} \;
    find /tests -type f -exec chmod 600 {} \;
    chmod 700 /tests/test.sh 2>/dev/null || true
fi

reward() {
    echo "$1" > /logs/verifier/reward.txt
    chmod 600 /logs/verifier/reward.txt 2>/dev/null || true
}

trap 'if [ ! -f /logs/verifier/reward.txt ]; then reward 0; fi' EXIT

python3 -m pytest /tests/test_fabric.py -q --ctrf /logs/verifier/ctrf.json
rc=$?
if [ "$rc" -eq 0 ]; then
    reward 1
else
    reward 0
fi
# Restore world-read on the log dir so the host collector can write reward.json.
# Nobody still cannot create files: directory is root-owned 755.
chmod 755 /logs/verifier 2>/dev/null || true
chmod 644 /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true
exit 0
