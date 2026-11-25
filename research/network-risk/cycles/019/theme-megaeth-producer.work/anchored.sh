#!/bin/bash
# Validate each listed block with the cycle 16 stateless-validator build (e1618ed7, mega-evm v1.7.3), anchored at the parent block:
# the witness pre-state is checked against the parent's state root, then block b is re-executed and its header compared.
# Usage: anchored.sh <blocklist> <outdir> <validator-binary>
R=https://mainnet.megaeth.com/rpc
G=/home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/sv/test_data/mainnet/genesis.json
BIN=${3:-/home/user/v4-core/research/network-risk/cycles/016/theme-megaeth-validator-build.work/build/target/release/stateless-validator}
mkdir -p $2
for b in $(cat $1); do
  p=$((b-1)); h=$(curl -s $R -H 'content-type: application/json' -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf 0x%x $p)\",false]}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['hash'])")
  rm -rf $2/d; timeout 300 $BIN --data-dir $2/d --genesis-file $G --rpc-endpoint $R --witness-endpoint $R --start-block $h --end-block $b > $2/$b.log 2>&1
  echo "$b exit=$? errs=$(grep -ci 'mismatch\|error' $2/$b.log) $(grep -o 'Validated block[^,]*' $2/$b.log | tail -1)"
  sleep 1
done
