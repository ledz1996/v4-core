#!/bin/bash
# Usage: runlist.sh <name> <block list>. Block-list replay through the census build of the public MegaETH validator.
W=$(dirname $(dirname $(realpath $0))); R=https://mainnet.megaeth.com/rpc; d=$W/runs/$1; mkdir -p $d
curl -s $R -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' > $d/client-before.json
CENSUS_OUT=$d/census.txt timeout 14400 $W/build/target/release/stateless-validator --data-dir $d/data --genesis-file $W/build/sv-census/test_data/mainnet/genesis.json --rpc-endpoint $R --witness-endpoint $R --block-list $2 --block-list-output-dir $d > $d/log.txt 2>&1
echo "exit $?" > $d/exit.txt
curl -s $R -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' > $d/client-after.json
rm -rf $d/data
