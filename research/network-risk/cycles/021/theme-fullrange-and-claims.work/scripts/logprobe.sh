# probe: eth_getLogs of the PoolManager Transfer topic over the newest N blocks on one endpoint
url=$1; pm=$2; n=$3
head=$(curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' $url | python3 -c "import json,sys;print(int(json.load(sys.stdin)['result'],16))")
lo=$((head-n+1))
curl -s -m 60 -X POST -H 'content-type: application/json' --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getLogs\",\"params\":[{\"address\":\"$pm\",\"topics\":[\"0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859\"],\"fromBlock\":\"$(printf 0x%x $lo)\",\"toBlock\":\"$(printf 0x%x $head)\"}]}" $url | head -c 300; echo
