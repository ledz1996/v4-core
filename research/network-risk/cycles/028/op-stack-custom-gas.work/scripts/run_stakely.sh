#!/bin/bash
W=/home/user/v4-core/research/network-risk/cycles/028/op-stack-custom-gas.work
for b in 7680d6d 3cbf835 06140ff; do
python3 $W/scripts/pinbatch.py $W/out/celo-$b-stakely-all.json https://celo-json-rpc.stakely.io $b hiword,extra,targeted,battery 600 120 3 > $W/out/celo-$b-stakely-all.log 2>&1 &
done
wait
