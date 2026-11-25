#!/bin/bash
W=/home/user/v4-core/research/network-risk/cycles/021/high-throughput.work
cd /home/user/v4-core/research/network-risk/tools/opdiff
V(){ for u in https://rpc.monad.xyz https://mainnet.megaeth.com/rpc https://ethereum-rpc.publicnode.com; do echo "$(date -u +%FT%TZ) $u $(curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' $u)"; done; }
V; python3 pmdiff.py $W/pmdiff.json 250 143 4326 > $W/pmdiff.log 2>&1
V; python3 pmdiff2.py $W/pmdiff2.json 300 143 4326 > $W/pmdiff2.log 2>&1
V; echo done
