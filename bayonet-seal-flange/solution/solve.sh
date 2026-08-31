#!/bin/bash
set -euo pipefail
mkdir -p /app
python3 /solution/build_pair.py --outdir /app
