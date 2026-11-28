#!/bin/bash
# cycle 39: reth v2.11.0 aarch64 handlers (ra64.py) on the eight vector sets of cycle 38, both families
cd "$(dirname "$0")/.."
D=$1
for s in battery targeted v4shapes c27 ruint121 provevec pow2 random; do echo $s; done | xargs -P 4 -I{} bash -c "python3 -I scripts/ra64.py $D {} out/reth-a64/{}.json >> out/reth-a64/progress.log 2>&1 || echo FAILED {} >> out/reth-a64/progress.log"
echo ALLDONE >> out/reth-a64/progress.log
