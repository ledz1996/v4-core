#!/bin/bash
# windows end at the head read at start; each chain runs independently
cd "$(dirname "$0")/.."
run() { c=$1; u=$2; pm=$3; w=$4; st=$5; H=$(curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' $u | python3 -c 'import sys,json;print(int(json.load(sys.stdin)["result"],16))'); STEP=$st timeout 3000 python3 -I scripts/depscan.py $c $u $pm $((H-w)) $H out/scan-$c.json > out/scan-$c.stdout 2>&1; }
run 8453 https://mainnet.base.org/ 0x498581ff718922c3f8e6a244956af099b2652b2b 20000 500 &
run 7777777 https://rpc.zora.energy/ 0x0575338e4c17006ae181b47900a84404247ca30f 3000000 20000 &
run 480 https://worldchain-mainnet.g.alchemy.com/public 0xb1860d529182ac3bc1f51fa2abd56662b7d13f33 1000000 5000 &
run 42220 https://forno.celo.org 0x288dc841A52FCA2707c6947B3A777c5E56cd87BC 1000000 5000 &
run 196 https://rpc.xlayer.tech 0x360e68faccca8ca495c1b759fd9eee466db9fb32 1000000 5000 &
run 4326 https://mainnet.megaeth.com/rpc 0xacb7e78fa05d562e0a5d3089ec896d57d057d38e 1000000 5000 &
wait
