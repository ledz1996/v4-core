#!/bin/bash
# Chain-following mode over consecutive blocks s..s+1999, anchored at the hash of block s-1: every witness pre-state
# is checked against the state root of the block before it. Usage: chain.sh <start> <end>
R=https://mainnet.megaeth.com/rpc; s=$1; e=$2; p=$((s-1))
h=$(curl -s $R -H 'content-type: application/json' -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf 0x%x $p)\",false]}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['hash'])")
D=/home/user/v4-core/research/network-risk/cycles/017/theme-library-paths.work/mega/chain-$s; rm -rf $D; mkdir -p $D
timeout 5400 /home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/target/release/stateless-validator --data-dir $D/data --genesis-file /home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/sv/test_data/mainnet/genesis.json --rpc-endpoint $R --witness-endpoint $R --start-block $h --end-block $e > $D/log.txt 2>&1
echo "$s..$e anchor=$h exit=$? $(grep -o 'Validated blocks this session[^\n]*' $D/log.txt | tail -1) errors=$(grep -ci 'mismatch\|ERROR' $D/log.txt)" >> /home/user/v4-core/research/network-risk/cycles/017/theme-library-paths.work/mega/chain-summary.txt
