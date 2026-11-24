"""Count swaps that share a block with earlier events of the same pool (state carried forward by log index),
and swaps whose pool had a ModifyLiquidity earlier in the same block (tick bitmap overlay used)."""
import json, glob, sys
sys.path.insert(0, '.')
import replay2 as R
out = {}
for f in sorted(glob.glob('raw/logs-*.json')):
    L = json.load(open(f)); cid = L['chainId']
    logs = sorted(L['logs'], key=lambda x: (int(x['blockNumber'], 16), int(x['logIndex'], 16)))
    seen = {}; shared = 0; overlay = 0; n = 0
    for x in logs:
        if x['topics'][0] not in (R.SWAP, R.MODIFY): continue
        k = (x['topics'][1], x['blockNumber']); prev = seen.setdefault(k, [])
        if x['topics'][0] == R.SWAP:
            n += 1
            if prev: shared += 1
            if R.MODIFY in prev: overlay += 1
        prev.append(x['topics'][0])
    out[cid] = {'swaps': n, 'afterEarlierEventSameBlock': shared, 'afterModifySameBlock': overlay}
    print(cid, out[cid])
json.dump(out, open('raw/inblock.json', 'w'), indent=1)
