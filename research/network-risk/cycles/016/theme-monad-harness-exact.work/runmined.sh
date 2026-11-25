#!/bin/bash
# replay of 2,007 mined Monad PoolManager transactions: interpreter vs native, and both against the block
cd "$(dirname "$0")"
BIN=${1:-rp}; OD=${2:-mined/out-v167}; mkdir -p $OD
for i in 0 1 2 3; do ./$BIN monad-pm-runtime.hex mined/part$i.txt > $OD/part$i.out 2> $OD/part$i.err & done; wait
grep -h "^txs=" $OD/part*.out > $OD/summary.txt
