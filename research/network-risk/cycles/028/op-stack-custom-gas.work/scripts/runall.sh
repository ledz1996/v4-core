#!/bin/bash
W=/home/user/v4-core/research/network-risk/cycles/028/op-stack-custom-gas.work
T=/home/user/v4-core/research/network-risk/tools/opdiff
O=$W/out; P="python3 $W/scripts/pinbatch.py"
$P $O/xlayer-hiword.json https://rpc.xlayer.tech f60420a hiword 600 40 3 > $O/xlayer-hiword.log 2>&1 &
$P $O/celo-reth-hiword-extra.json https://forno.celo.org 74cc8bb hiword,extra 600 60 3 > $O/celo-reth-hiword-extra.log 2>&1 &
$P $O/celo-geth-all.json https://forno.celo.org Geth/v0.1.0 hiword,extra,targeted,battery 600 60 3 > $O/celo-geth-all.log 2>&1 &
$P $O/celo-1rpc-all.json https://1rpc.io/celo 7680d6d hiword,extra,targeted,battery 300 60 2 > $O/celo-1rpc-all.log 2>&1 &
(cd $T; python3 battery.py $O/battery.json 42220 196 > $O/battery.log 2>&1; python3 targeted.py $O/targeted.json 42220 196 > $O/targeted.log 2>&1) &
(cd $T; python3 pmdiff.py $O/pmdiff.json 250 42220 196 > $O/pmdiff.log 2>&1; python3 pmdiff2.py $O/pmdiff2.json 300 42220 196 > $O/pmdiff2.log 2>&1) &
(cd $T; python3 swaps.py $O/swaps.json 42220 196 > $O/swaps.log 2>&1; python3 replay.py $O/swaps.json $O/replay.json > $O/replay.log 2>&1) &
wait
echo DONE > $O/all.done
