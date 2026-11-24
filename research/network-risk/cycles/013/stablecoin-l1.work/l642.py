"""L-642: compare the Python transcription rapid_micro in cycles/011/theme-keccak-cache.work/keccak_buckets.py with
rapidhash 4.4.1 compiled from the crate (v3::rapidhash_v3_micro_inline::<false,false>, RapidSecrets::seed(0)).
Usage: l642.py <rust_binary> <out.json>"""
import sys, json, random, subprocess
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/011/theme-keccak-cache.work')
import keccak_buckets as K
binp, out = sys.argv[1], sys.argv[2]
recs, meta = K.build()
inputs = []
seen = set()
for seq in recs:
    for d in seq:
        if d not in seen: seen.add(d); inputs.append(d)
rnd = random.Random(642)
for ln in range(0, 129):
    for _ in range(200): inputs.append(bytes(rnd.getrandbits(8) for _ in range(ln)))
p = subprocess.run([binp], input='\n'.join(d.hex() for d in inputs) + '\n', capture_output=True, text=True, check=True)
rust = [int(x, 16) for x in p.stdout.split()]
assert len(rust) == len(inputs)
bad = [(d.hex(), hex(r), hex(K.rapid_micro(d))) for d, r in zip(inputs, rust) if r != K.rapid_micro(d)]
lens = sorted({len(d) for d in inputs})
designed = sum(len(set(s)) for s in recs)
json.dump({'inputs': len(inputs), 'lengths': [lens[0], lens[-1]], 'designedRecordInputs': designed, 'mismatches': len(bad), 'examples': bad[:10], 'meta': meta}, open(out, 'w'), indent=1)
print('inputs', len(inputs), 'lengths', lens[0], '-', lens[-1], 'mismatches', len(bad), 'colliding buckets in designed set', meta['collidingBuckets'])
