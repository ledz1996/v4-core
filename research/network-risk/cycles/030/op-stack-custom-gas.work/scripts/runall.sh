#!/bin/bash
# Cycle 30 op-stack-custom-gas: standard reruns for chain ids 42220 and 196, outputs in the work directory.
W=/home/user/v4-core/research/network-risk/cycles/030/op-stack-custom-gas.work
T=/home/user/v4-core/research/network-risk/tools/opdiff
O=$W/out
(cd $T; python3 battery.py $O/battery.json 42220 196 > $O/battery.log 2>&1; python3 targeted.py $O/targeted.json 42220 196 > $O/targeted.log 2>&1) &
(cd $T; python3 pmdiff.py $O/pmdiff.json 250 42220 196 > $O/pmdiff.log 2>&1; python3 pmdiff2.py $O/pmdiff2.json 300 42220 196 > $O/pmdiff2.log 2>&1) &
(cd $T; python3 swaps.py $O/swaps.json 42220 196 > $O/swaps.log 2>&1; python3 replay.py $O/swaps.json $O/replay.json > $O/replay.log 2>&1) &
wait
echo DONE > $O/all.done
