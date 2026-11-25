#!/bin/bash
cd /home/user/v4-core/research/network-risk/tools/opdiff
O=/home/user/v4-core/research/network-risk/cycles/020/op-stack-custom-gas.work/out
python3 battery.py $O/battery.json 42220 196 > $O/battery.log 2>&1 &
python3 targeted.py $O/targeted.json 42220 196 > $O/targeted.log 2>&1 &
python3 /home/user/v4-core/research/network-risk/cycles/020/op-stack-custom-gas.work/scripts/pin.py reth battery.py $O/battery-celo-reth.json 42220 > $O/battery-celo-reth.log 2>&1 &
python3 /home/user/v4-core/research/network-risk/cycles/020/op-stack-custom-gas.work/scripts/pin.py Geth battery.py $O/battery-celo-geth.json 42220 > $O/battery-celo-geth.log 2>&1 &
python3 pmdiff.py $O/pmdiff.json 250 42220 196 > $O/pmdiff.log 2>&1 &
python3 pmdiff2.py $O/pmdiff2.json 300 42220 196 > $O/pmdiff2.log 2>&1 &
wait
python3 swaps.py $O/swaps.json 42220 196 > $O/swaps.log 2>&1
python3 replay.py $O/swaps.json $O/replay.json > $O/replay.log 2>&1
echo DONE
