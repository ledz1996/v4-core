"""Monad pool list for Task 2 without a full Initialize census (eth_getLogs is limited to 100 blocks there): Initialize logs in
cycle 30's log dump since v0.16.7 (cycles/030/theme-monad-mined-native-coverage.work/out/monad-logs-since-0.16.7.json) and the
22 pool keys of cycle 9 (cycles/009/high-throughput.work/raw/invariants_143.json). Pools seen only in Swap logs have no key
and are counted. Writes out/pools-monad.json in the layout of pools.py; refine.py reads current state."""
import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
TI = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
TS = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
d = json.load(open('/home/user/v4-core/research/network-risk/cycles/030/theme-monad-mined-native-coverage.work/out/monad-logs-since-0.16.7.json'))
logs = d if isinstance(d, list) else (d.get('logs') or [x for v in d.values() if isinstance(v, list) for x in v])
pools = {}; swapIds = set(); nlogs = 0; blocks = set()
for l in logs:
    if not isinstance(l, dict) or 'topics' not in l: continue
    nlogs += 1; blocks.add(l.get('blockNumber') or l.get('block'))
    t = l['topics']
    if t and t[0] == TI:
        b = bytes.fromhex(l['data'][2:])
        pools[t[1]] = {'currency0': '0x' + t[2][-40:], 'currency1': '0x' + t[3][-40:], 'fee': int.from_bytes(b[0:32], 'big'),
                       'tickSpacing': int.from_bytes(b[32:64], 'big', signed=True), 'hooks': '0x' + b[64:96].hex()[-40:], 'block': l.get('blockNumber') or l.get('block'), 'src': 'c30-initialize'}
    elif t and t[0] == TS: swapIds.add(t[1])
c9 = json.load(open('/home/user/v4-core/research/network-risk/cycles/009/high-throughput.work/raw/invariants_143.json'))['pools']
for p in c9:
    k = p['key']; pools.setdefault(p['pool'], {'currency0': k['currency0'], 'currency1': k['currency1'], 'fee': k['fee'], 'tickSpacing': k['tickSpacing'], 'hooks': k['hooks'], 'src': 'c9'})
print('logs', nlogs, 'blocks', len(blocks), 'pools with key', len(pools), 'swap-only ids without key', len(swapIds - set(pools)))
json.dump({'label': 'monad', 'pools': pools, 'swapIdsWithoutKey': sorted(swapIds - set(pools)), 'logsRead': nlogs}, open('out/pools-monad-keys.json', 'w'), indent=1)
