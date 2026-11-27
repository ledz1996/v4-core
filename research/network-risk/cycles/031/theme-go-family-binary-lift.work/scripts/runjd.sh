#!/bin/bash
# Task 3 and the jump analysis faults: every target with no fault, the PUSH1 bound fault and one flipped bitmap bit
cd "$(dirname "$0")/.."
for t in bsc-amd64 bor-amd64 avax-amd64 bsc-arm64 bor-arm64 avax-arm64; do for f in none opcode bit; do
  [ -s out/jd/$t-$f.json ] && continue
  echo "$t $f"; done; done | xargs -P 2 -L 1 bash -c 'python3 -I scripts/jd.py $0 out/jd/$0-$1.json $1 >> out/jd/progress.log 2>&1 || echo "FAILED $0 $1" >> out/jd/progress.log'
echo ALLDONE >> out/jd/progress.log
