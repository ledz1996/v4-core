"""Index of the Swap logs of the two Algebra Integral factories in the cycle 15 window (no RPC), and the seeded sample."""
import json, random, collections
F = {'0xf77bd082c627aa54591cf2f2eaa811fd1ab3b1f3': 'v1.1', '0x5f95e92c338e6453111fc55ee66d4aafcce661a7': 'v1.2.2'}
em = json.load(open('out/emitters.json'))
alg = {a: em[a]['factory'] for a in em if em[a]['factory'] in F}
sw = []; mb = collections.Counter()
for line in open('/home/user/v4-core/research/network-risk/cycles/015/theme-closed-producers-2.work/raw/logs999.jsonl'):
    for r in json.loads(line)['rows']:
        if r[4] in alg:
            if r[0] == 'S': sw.append((r[4], r[1], r[2], r[3]))
            else: mb[r[0]] += 1
sw.sort()
SEED = 19
samp = sorted(random.Random(SEED).sample(sw, 20000))
groups = sorted(set((s[0], s[1]) for s in samp))
fc = collections.Counter(alg[s[0]] for s in sw)
json.dump({'seed': SEED, 'pools': alg, 'swapsInWindow': len(sw), 'swapsByFactory': fc, 'mintBurnRows': mb,
           'sampleSwaps': samp, 'groups': groups}, open('out/alg-sample.json', 'w'))
print(len(alg), 'pools', len(sw), 'swaps', dict(fc), dict(mb), 'sample groups', len(groups))
