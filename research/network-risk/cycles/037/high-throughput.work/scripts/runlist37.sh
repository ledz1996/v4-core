#!/bin/bash
# cycle 37: block-list replay of new MegaETH PoolManager blocks through the cycle 33 census build of the public stateless validator; outputs in this work dir
C=/home/user/v4-core/research/network-risk/cycles/033/theme-closed-producer-operand-census.work
W=/home/user/v4-core/research/network-risk/cycles/037/high-throughput.work; R=https://mainnet.megaeth.com/rpc; d=$W/out/census-$1; mkdir -p $d
curl -s $R -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' > $d/client-before.json
CENSUS_OUT=$d/census.txt timeout 7200 $C/build/target/release/stateless-validator --data-dir $d/data --genesis-file $C/build/sv-census/test_data/mainnet/genesis.json --rpc-endpoint $R --witness-endpoint $R --block-list $2 --block-list-output-dir $d > $d/log.txt 2>&1
echo "exit $?" > $d/exit.txt
curl -s $R -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}' > $d/client-after.json
rm -rf $d/data
