#!/bin/bash
# ./tools/runmined.sh BUILD OUTDIR : the 2,007 mined Monad PoolManager transactions stored by cycle 16, four parts in parallel,
# with native block coverage written to OUTDIR/partN.cov
cd "$(dirname "$0")/.."
B=$1; OD=$2; C16=../../016/theme-monad-harness-exact.work; mkdir -p $OD
for i in 0 1 2 3; do HX_COVTMP=$OD HX_COVOUT=$OD/part$i.cov ./build/$B/rp monad-pm-runtime.hex $C16/mined/part$i.txt > $OD/part$i.out 2> $OD/part$i.err & done; wait
grep -h "^txs=" $OD/part*.out > $OD/summary.txt
