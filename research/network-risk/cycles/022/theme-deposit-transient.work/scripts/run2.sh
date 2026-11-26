#!/bin/bash
cd "$(dirname "$0")/.."
head() { curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' $1 | python3 -c 'import sys,json;print(int(json.load(sys.stdin)["result"],16))'; }
H=$(head https://base-rpc.publicnode.com); STEP=200 timeout 3000 python3 -I scripts/depscan.py 8453 https://base-rpc.publicnode.com 0x498581ff718922c3f8e6a244956af099b2652b2b $((H-6000)) $H out/scan-8453.json > out/scan-8453.stdout 2>&1 &
H=$(head https://worldchain-mainnet.g.alchemy.com/public); STEP=100 timeout 3000 python3 -I scripts/depscan.py 480 https://worldchain-mainnet.g.alchemy.com/public 0xb1860d529182ac3bc1f51fa2abd56662b7d13f33 $((H-100000)) $H out/scan-480.json > out/scan-480.stdout 2>&1 &
H=$(head https://mainnet.megaeth.com/rpc); BLOCKMODE=1 BSIZE=5 STEP=5000 timeout 3000 python3 -I scripts/depscan.py 4326 https://mainnet.megaeth.com/rpc 0xacb7e78fa05d562e0a5d3089ec896d57d057d38e $((H-1000000)) $H out/scan-4326.json > out/scan-4326.stdout 2>&1 &
wait
