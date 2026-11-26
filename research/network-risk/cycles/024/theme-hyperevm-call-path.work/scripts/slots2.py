# Task 3 (L-1017): cycle 23 slot set plus every bitmap word between each swap's start and end tick.
# Start tick of a swap = tick after the previous Swap of the same pool, or the Initialize tick.
# Bitmap word key: keccak(wordPos, poolBase + 5), wordPos = compress(tick, spacing) >> 8
# (src/libraries/TickBitmap.sol:16-38, src/libraries/Pool.sol:83-91 field order).
# Logs: cycle 23 whole-history file plus logs fetched now from its toBlock+1 to head on the replica.
import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-hyperevm-twin-state.work/scripts')
from slots import derive, SIG, sx, compress, h, w, M
from rpc import rpc
C23 = '/home/user/v4-core/research/network-risk/cycles/023/theme-hyperevm-twin-state.work/raw/pm_logs_all_hyperlend.json'
R = sys.argv[1]; out = sys.argv[2]
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
d = json.load(open(C23))
logs = list(d['logs'])
head = int(rpc(R, 'eth_blockNumber', []), 16)
new = []
b = d['toBlock'] + 1
while b <= head:
    e = min(b + 49999, head)
    new += rpc(R, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(e)}], timeout=120)
    b = e + 1
logs += new
logs.sort(key=lambda l: (int(l['blockNumber'], 16), int(l['logIndex'], 16)))
slots, pools, cur = derive(logs)
base = len(slots)
last = {}
added = 0; pairs = 0; capped = []
CAP = 4096
for l in logs:
    k = SIG.get(l['topics'][0]); dd = l['data'][2:]; words = [dd[i:i + 64] for i in range(0, len(dd), 64)]
    pid = int(l['topics'][1], 16) if len(l['topics']) > 1 else None
    if k == 'Initialize':
        last[pid] = sx(words[4], 24)
    elif k == 'Swap':
        t = sx(words[4], 24)
        if pid in last and pid in pools:
            sp = pools[pid]['sp']
            a, z = sorted((compress(last[pid], sp) >> 8, compress(t, sp) >> 8))
            pairs += 1
            if z - a > CAP:
                capped.append([hex(pid), last[pid], t, z - a]); z = a + CAP
            pb = h(w(pid), w(6))
            for wp in range(a, z + 1):
                key = h(w(wp), w(pb + 5))
                if key not in slots:
                    slots[key] = f'pool {pid:#066x} bitmap word {wp} (range)'; added += 1
        last[pid] = t
json.dump({'head': head, 'newLogs': len(new), 'newLogBlocks': sorted({int(x['blockNumber'], 16) for x in new}),
           'baseSlots': base, 'rangeWordsAdded': added, 'swapPairs': pairs, 'capped': capped,
           'slots': {hex(k): v for k, v in slots.items()}, 'pools': {hex(k): v for k, v in pools.items()},
           'currencies': ['0x%040x' % c for c in sorted(cur)]}, open(out, 'w'), indent=0)
print('head', head, 'new logs', len(new), 'base', base, 'added', added, 'pairs', pairs, 'capped', len(capped))
