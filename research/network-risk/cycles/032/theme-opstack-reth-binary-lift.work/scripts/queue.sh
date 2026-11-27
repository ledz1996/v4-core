#!/bin/sh
# runs the remaining arithmetic batteries, four shards each, one binary at a time
cd "$(dirname "$0")/.."
while pgrep -f "arith.py build/opreth-amd64.cfg.json" >/dev/null; do sleep 20; done
for n in base-amd64 opreth-arm64 base-arm64; do
  for i in 0 1 2 3; do python3 -I scripts/arith.py build/$n.cfg.json out/arith-$n-$i.json all none $i 4 > out/arith-$n-$i.log 2>&1 & done
  wait
done
