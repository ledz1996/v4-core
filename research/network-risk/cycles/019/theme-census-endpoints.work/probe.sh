for u in https://rpc.hyperliquid.xyz/evm https://rpc.purroofgroup.com https://rpc.monad.xyz https://rpc-mainnet.monadinfra.com https://mainnet.megaeth.com/rpc https://rpc.mainnet.tempo.xyz https://rpc.mainnet.arc.io https://forno.celo.org https://rpc.xlayer.tech https://mainnet.unichain.org https://base.api.pocket.network https://mainnet.base.org https://api.avax.network/ext/bc/C/rpc https://avax.api.pocket.network; do
 for m in web3_clientVersion eth_blockNumber; do
  echo "$u $m $(curl -s -m 20 -H 'content-type: application/json' -A rpc-client --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$m\",\"params\":[]}" $u | head -c 200)"
 done
 echo "$u receipts $(curl -s -m 20 -H 'content-type: application/json' -A rpc-client --data '{"jsonrpc":"2.0","id":1,"method":"eth_getBlockReceipts","params":["latest"]}' $u | head -c 120)"
done
