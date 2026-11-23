# Candidate table: the 20 hooks with the largest priced holdings per network, with code size, flags and pool count.
import sys, glob
from common import *
os.chdir(C5)
from summ import census, flags
os.chdir(HERE)
SKIP = {'0x0000000000000000000000000000000000000020'}
NAMED = {99901: ['0x6b1216a40b65c83e9c9e18a562c446697b8cf8ec', '0xe0def4221b9840a610d4e7d55812a79a6431a8ec', '0x3ab88ddc3cf2a012af88b60828edb4553697e5dc'],
         4663: ['0x75a54357d9c78a2db19004a5fdc76c50f9242aec', '0xe5e702641ea86f4ae6cc3cdaed2b886f976be044', '0x4eb1976978756bd56802d8162f2271844924e0cc', '0x2c668601193e4a081dd82604785e436aff6a2acc'],
         5042: ['0x20eead6db6b3d0a4491e9073119dd0ebff166acc', '0x4ab0bf61327761fffc5910052d9e0b9a94f960cc'],
         196: ['0x9a935223eabd30b00fa680a5f3f8e7485e26aacc'], 1: ['0x322dcec4958c14e021a9f1cd49df11b9457968cc'],
         8453: ['0x0469a4bd3724dc86c9542f4694c976da13c450c0', '0x5e320ea6278107968c119942e57d876c5f922acc']}
out = []
for n in NETS:
    cid = n['chainId']
    try: v = json.load(open(os.path.join(RAW, 'value_%d.json' % cid)))
    except Exception: continue
    cs = json.load(gzip.open(os.path.join(RAW, 'codesize_%d.json.gz' % cid)))
    os.chdir(C5); cnt = census(cid)[0]; os.chdir(HERE)
    by = {r['hook']: r for r in v['rank']}
    top = [r['hook'] for r in v['rank'] if r['hook'] not in SKIP and cs['byHook'].get(r['hook'], 0) > 0 and r['usd'] > 0][:20]
    for h in NAMED.get(cid, []):
        if h not in top: top.append(h)
    fam = {}
    for g in cs['groups']: fam[(g['size'], g['flags'])] = g['n']
    for h in top:
        r = by.get(h, dict(usd=0, claimsUsd=0, items=[]))
        sz = cs['byHook'].get(h, -1); fl = hex(int(h, 16) & 0x3fff)
        out.append(dict(chainId=cid, hook=h, usd=r['usd'], claimsUsd=r['claimsUsd'], size=sz, flags=fl, fl=','.join(flags(h)), pools=cnt.get(h, 0), family=fam.get((sz, fl), 1),
                        items=[[k, s or c, '%.6g' % (int(v_) / 10 ** (d if d is not None else 18)), round(x, 2)] for x, k, c, s, d, v_, how in r['items'][:6]]))
json.dump(out, open(os.path.join(RAW, 'cand.json'), 'w'), indent=0)
print(len(out))
for o in out:
    if len(sys.argv) > 1 and str(o['chainId']) != sys.argv[1]: continue
    print(o['chainId'], o['hook'], '%10.0f' % o['usd'], 'size', o['size'], o['fl'], 'pools', o['pools'], 'fam', o['family'])
