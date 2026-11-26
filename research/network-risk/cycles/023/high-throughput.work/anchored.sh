#!/bin/bash
# Same as cycles/016/theme-megaeth-validator-build.work/anchored.sh, cycle 23 copy; run with that cycle's build (stateless-validator e1618ed7, mega-evm v1.7.3).
R=https://mainnet.megaeth.com/rpc
for b in $(cat $1); do
  p=$((b-1)); h=$(curl -s $R -H 'content-type: application/json' -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf 0x%x $p)\",false]}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['hash'])")
  rm -rf /home/user/v4-core/research/network-risk/cycles/023/high-throughput.work/anch/d; timeout 300 /home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/target/release/stateless-validator --data-dir /home/user/v4-core/research/network-risk/cycles/023/high-throughput.work/anch/d --genesis-file /home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/sv/test_data/mainnet/genesis.json --rpc-endpoint $R --witness-endpoint $R --start-block $h --end-block $b > /home/user/v4-core/research/network-risk/cycles/023/high-throughput.work/anch/$b.log 2>&1
  echo "$b exit=$? $(grep -ci 'mismatch\|error' /home/user/v4-core/research/network-risk/cycles/023/high-throughput.work/anch/$b.log) $(grep -o 'Validated blocks[^\n]*count=[0-9]*' /home/user/v4-core/research/network-risk/cycles/023/high-throughput.work/anch/$b.log | tail -1)"
done
