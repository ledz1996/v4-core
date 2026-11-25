#!/bin/bash
# Chain-following mode anchored at the parent block: checks the witness pre-state against the parent's state root, then validates block b.
R=https://mainnet.megaeth.com/rpc
W=$(dirname $(realpath $0)); mkdir -p $W/anch
for b in $(cat $1); do
  p=$((b-1)); h=$(curl -s $R -H 'content-type: application/json' -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf 0x%x $p)\",false]}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['hash'])")
  rm -rf $W/anch/d; timeout 300 $W/build/target/release/stateless-validator --data-dir $W/anch/d --genesis-file $W/build/sv/test_data/mainnet/genesis.json --rpc-endpoint $R --witness-endpoint $R --start-block $h --end-block $b > $W/anch/$b.log 2>&1
  echo "$b exit=$? $(grep -ci 'mismatch\|error' $W/anch/$b.log) $(grep -o 'Validated block[^,]*' $W/anch/$b.log | tail -1)"
done
