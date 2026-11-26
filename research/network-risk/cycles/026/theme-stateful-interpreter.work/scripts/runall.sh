#!/bin/sh
# all 21 networks, four at a time; Polygon additionally on each public endpoint
cd "$(dirname "$0")/.."
python3 -c "
import json;[print(n['chainId']) for n in json.load(open('../../../state/networks.json'))['networks'] if n['chainId']!=1]" \
 | xargs -P 4 -I{} sh -c 'python3 -I scripts/chainrun.py out {} auto > out/logs/run-{}.log 2>&1'
for u in https://rpc-mainnet.matic.quiknode.pro https://polygon.drpc.org https://poly.api.pocket.network; do
  python3 -I scripts/chainrun.py out 137 $u > out/logs/run-137-$(echo $u | cut -d/ -f3).log 2>&1
done
echo ALLDONE
