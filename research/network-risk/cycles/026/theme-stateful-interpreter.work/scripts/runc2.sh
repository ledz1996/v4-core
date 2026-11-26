#!/bin/sh
# sequence c2 (beforeSwap hook writes slot0 in a nested frame) on 20 networks, Tempo's smaller variants, then Ethereum's
# erigon backends behind the Pocket gateway (repeated until both brackets name erigon, at most 12 times)
cd "$(dirname "$0")/.."
python3 -c "
import json;[print(n['chainId']) for n in json.load(open('../../../state/networks.json'))['networks'] if n['chainId'] not in (1,137)]" \
 | xargs -P 4 -I{} sh -c 'python3 -I scripts/chainrun.py out {} auto c2 > out/logs/c2-{}.log 2>&1'
python3 -I scripts/chainrun.py out 4217 auto a64t bt d40 > out/logs/tempo-small.log 2>&1
python3 -I scripts/chainrun.py out 1 https://eth.api.pocket.network c2 > out/logs/c2-1.log 2>&1
echo C2DONE
