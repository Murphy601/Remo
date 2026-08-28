#!/bin/bash
set -u
mkdir -p /logs/verifier /tmp/cdc_build

reward() {
    echo "$1" > /logs/verifier/reward.txt
}

trap 'if [ ! -f /logs/verifier/reward.txt ]; then reward 0; fi' EXIT

python3 -m pytest /tests/test_fabric.py -q --ctrf /logs/verifier/ctrf.json
rc=$?
if [ "$rc" -eq 0 ]; then
    reward 1
else
    reward 0
fi
exit 0
