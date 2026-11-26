#!/bin/sh
# reference runs at each network's PoolManager address (immutable differs), two at a time
cd "$(dirname "$0")"
python3 -c "
import json;[print(n['chainId'],n['poolManager']) for n in json.load(open('../../../../state/networks.json'))['networks']]" | while read cid pm; do
  echo "$cid $pm"
done | xargs -P 2 -L 1 sh -c 'nice python3 refrun.py ../out/allcases.json ../out/ref-$0.json $1 1 > ../out/logs/ref-$0.log 2>&1'
