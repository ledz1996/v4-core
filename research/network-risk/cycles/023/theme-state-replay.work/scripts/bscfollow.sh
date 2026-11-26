#!/bin/bash
# BNB Smart Chain follow mode: public trace endpoints keep state for recent blocks only, so the window is rebuilt from
# the head every round (3,000 newest PoolManager transactions) and traced newest first. Earlier windows are kept.
cd "$(dirname "$0")"
for r in $(seq 1 8); do
  [ -f ../raw/56/window.json ] && mv ../raw/56/window.json ../raw/56/window-round-$(date +%s).json
  timeout 420 python3 collect.py 56 3000 8 >> ../raw/collect-56.log 2>&1
done
