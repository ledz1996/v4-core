#!/bin/bash
# cycle 38 Task 3: erigon kernels (ejd.py) and the geth jump analysis (jd.py), each with no fault and planted faults
cd "$(dirname "$0")/.."
for f in none opcode bit sse; do python3 -I scripts/ejd.py out/jd/erigon-amd64-$f.json $f >> out/jd/progress.log 2>&1; done
for t in geth-amd64 geth-arm64; do for f in none opcode bit; do python3 -I scripts/jd.py $t out/jd/$t-$f.json $f >> out/jd/progress.log 2>&1 || echo "FAILED $t $f" >> out/jd/progress.log; done; done
echo ALLDONE >> out/jd/progress.log
