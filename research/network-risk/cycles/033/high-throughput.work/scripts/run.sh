#!/bin/bash
# cycle 33 reruns for chain ids 143 and 4326
W=/home/user/v4-core/research/network-risk/cycles/033/high-throughput.work/out
S=/home/user/v4-core/research/network-risk/cycles/031/high-throughput.work/scripts
cd /home/user/v4-core/research/network-risk/tools/opdiff
V(){ for u in https://rpc.monad.xyz https://rpc-mainnet.monadinfra.com https://mainnet.megaeth.com/rpc; do echo "$(date -u +%FT%TZ) $u $(curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' $u)"; done; }
V; python3 battery.py $W/battery.json 143 4326 > $W/battery.log 2>&1
V; python3 targeted.py $W/targeted.json 143 4326 > $W/targeted.log 2>&1
V; python3 pmdiff.py $W/pmdiff.json 250 143 4326 > $W/pmdiff.log 2>&1
V; python3 pmdiff2.py $W/pmdiff2.json 300 143 4326 > $W/pmdiff2.log 2>&1
V; ALT143=https://rpc-mainnet.monadinfra.com python3 $S/wrap143.py swaps.py $W/swaps.json 143 4326 > $W/swaps.log 2>&1
V; ALT143=https://rpc-mainnet.monadinfra.com python3 $S/wrap143.py replay.py $W/swaps.json $W/replay.json > $W/replay.log 2>&1
V; python3 pmdiff6.py $W/pmdiff6.json 143 4326 > $W/pmdiff6.log 2>&1
V; echo done
