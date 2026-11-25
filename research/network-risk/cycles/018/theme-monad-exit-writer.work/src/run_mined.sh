#!/bin/bash
# Mined Monad PoolManager transactions of cycle 16 (2,007 txs) replayed by the instrumented v0.16.5 build under
# forced writer orders: interpreter vs native per frame, both vs the block. Orders: map order, permutation indices
# 1..5 (mode 1), shuffle seeds 101..106 (mode 2), and the planted fault 3 with seed 1.
W=$(cd "$(dirname "$0")/.." && pwd); cd $W/../../016/theme-monad-harness-exact.work; OD=$W/out/mined2; mkdir -p $OD
jobs=""
for o in "0 0" "1 1" "1 2" "1 3" "1 4" "1 5" "2 101" "2 102" "2 103" "2 104" "2 105" "2 106" "F3 1"; do
  set -- $o; m=$1; k=$2; F=0; [ $m = F3 ] && { m=2; F=3; }
  for i in 0 1 2 3; do jobs="$jobs $m:$k:$F:$i"; done
done
echo $jobs | tr ' :' '\n ' | xargs -P 4 -L 1 sh -c 'HXW_FAULT=$2 HXW_MODE=$0 HXW_K=$1 '$W'/build/replay-165w monad-pm-runtime.hex mined/part$3.txt > '$OD'/m$0-k$1-f$2-part$3.out 2> '$OD'/m$0-k$1-f$2-part$3.err'
for f in $OD/*.out; do echo "$(basename $f) $(grep '^txs=' $f)"; done > $OD/summary.txt
