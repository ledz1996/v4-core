"""Decode script 189 of set 2 (seed 11_2026_11_24) and the stored full Ethereum answer (cycle 18 blastapi run) per call."""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pmdiff2 as Q, pmdiff as P
rnd = random.Random(11_2026_11_24); sc = [Q.script(rnd, i) for i in range(300)]
data, kinds, meta = sc[189]
print('C0', hex(P.C0), 'meta', meta, 'calls', len(kinds))
ref = json.load(open('/home/user/v4-core/research/network-risk/cycles/018/theme-full-range-swaps.work/raw/eth-blast-s2.json'))['scripts']['189']['plain']
recs = Q.parse(bytes.fromhex(ref[2:]))
i = 0; off = 0
while True:
    tgt = data[off:off+20]; n = int.from_bytes(data[off+20:off+22], 'big')
    if n == 0: break
    cd = data[off+22:off+22+n]; off += 22 + n
    ok, ret = recs[i] if i < len(recs) else (None, b'')
    print(i, kinds[i], tgt[-4:].hex(), cd[:4].hex(), 'ok', ok, ret[:68].hex())
    i += 1
print('records', len(recs))
