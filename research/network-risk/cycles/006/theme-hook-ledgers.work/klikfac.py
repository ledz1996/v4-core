# L-378: for each Klik hook, read factory(), launchEnabled(), and what the factory holds in the pair currencies of the hook's pools. Read-only.
import sys, collections
from common import *
os.chdir(C5)
from summ import census, load
os.chdir(HERE)
import value as V
HOOKS = {1: ['0x1d06faa7ff674ccfd8a5736c0c0973cb0a8fa0cc', '0x6d01769ab90674d0d56b155f57003284e1b460cc', '0xcba49142a75da64a679f32a159f4316f11a7e0cc'], 8453: ['0x5b0a864213d49f23ed2a6635cc42b3b4fe7720cc', '0x64746dca345c5652bc251597bd99562216a7a0cc'], 130: ['0x9463925bdeee2be5eade2a60857442b4a15ca0cc'], 57073: ['0x71b7a448b96a01de73b0caf1267d33558d2620cc'], 42161: ['0x71b7a448b96a01de73b0caf1267d33558d2620cc'], 4663: ['0x41b82571eaaed65f18ad3428f066cd23b9b3a0cc'], 43114: ['0xb2c964edbac922f006a09bd293b6c42ee147e0cc'], 143: ['0xdd1e195f536e5375ada2eeb179270ac23af8e0cc'], 4217: ['0x50995539e4afaca479bb59b0d795d94e0efea0cc']}
out = []
for cid, hs in HOOKS.items():
    n = net(cid); us = urls(cid); u = us[0]
    os.chdir(C5); rows = load(cid); os.chdir(HERE)
    for h in hs:
        try:
            fac = '0x' + call(u, h, 'factory()')[-40:]
            ver = call(u, h, 'VERSION()'); 
            try: le = int(call(u, fac, 'launchEnabled()'), 16)
            except Exception: le = None
            R = [r for r in rows if r[6] == h]
            pairs = collections.Counter(r[2] for r in R)
            bn = int(rpc(u, 'eth_blockNumber', []), 16)
            res = {}
            calls = [(MC3, '4d2301cc' + adr(fac))] + [(c, '70a08231' + adr(fac)) for c in pairs if int(c, 16)] + [(c, '313ce567') for c in pairs if int(c, 16)] + [(c, '95d89b41') for c in pairs if int(c, 16)]
            r = mc3(u, calls); toks = [c for c in pairs if int(c, 16)]
            nat = int(r[0][1][:64], 16) if r[0][0] else 0
            held = []
            for i, c in enumerate(toks):
                ok, b = r[1 + i]; v = int(b[:64], 16) if ok and len(b) >= 64 else 0
                ok2, d = r[1 + len(toks) + i]; dec = int(d[:64], 16) if ok2 and len(d) >= 64 else 18
                ok3, s = r[1 + 2 * len(toks) + i]
                try: sym = bytes.fromhex(s[128:128 + 2 * int(s[64:128], 16)]).decode('utf8', 'replace') if ok3 and len(s) >= 128 else ''
                except Exception: sym = ''
                if v: held.append((c, sym, v / 10 ** dec, v))
            px = V.ds(V.SLUG[cid], [c for c, _, _, _ in held]) if held else {}
            usd = sum(min(a * px[c][0], px[c][1] / 2) for c, s, a, v in held if c in px)
            o = dict(chainId=cid, hook=h, factory=fac, block=bn, launchEnabled=le, pools=len(R), native=nat, held=held, tokenUsd=round(usd, 2), priced=len(px))
            out.append(o)
            print(cid, h, 'factory', fac, 'launchEnabled', le, 'pools', len(R), 'block', bn, 'native', nat / 1e18, 'tokens held', [(s, round(a, 6)) for c, s, a, v in held][:12], 'tokenUsd', round(usd, 2))
        except Exception as e:
            print(cid, h, 'ERR', repr(e)[:200])
json.dump(out, open(os.path.join(RAW, 'klik_factories.json'), 'w'), indent=1)
