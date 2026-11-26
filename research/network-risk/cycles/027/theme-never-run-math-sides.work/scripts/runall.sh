#!/bin/bash
# Task 2: run the cycle 27 cases through eth_call (read-only, state overrides) on all 21 networks with the cycle 25 driver
# runner (cycles/025/theme-unexecuted-sides.work/scripts/chainrun.py). Every batch is bracketed by web3_clientVersion.
W=/home/user/v4-core/research/network-risk/cycles/027/theme-never-run-math-sides.work
CR=/home/user/v4-core/research/network-risk/cycles/025/theme-unexecuted-sides.work/scripts/chainrun.py
for kv in $(cat $W/out/rpcs.txt); do
  cid=${kv%%=*}; url=${kv#*=}
  ( GAS=25000000 BS=8 python3 $CR $W/out/run27/allcases.json $W/out/run27 $cid $url > $W/out/run27/log-$cid.txt 2>&1;
    GAS=25000000 BS=1 python3 $CR $W/out/run27b/allcases.json $W/out/run27b $cid $url > $W/out/run27b/log-$cid.txt 2>&1 ) &
done
wait
