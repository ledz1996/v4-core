# Find other deployments of the Klik multichain hook: hooks whose flags equal 0x20cc and that answer VERSION() and pendingClaims(address). Read-only.
import sys, json, concurrent.futures as cf
from lib import *
from config import CFG
from summ import census
from probe import ecall
def s(x):
    try:
        b = bytes.fromhex(x[2:]); l = int.from_bytes(b[32:64], 'big'); return b[64:64 + l].decode('utf8', 'replace')
    except Exception: return None
def one(cid):
    n = net(cid); u = n['rpc']; out = []
    try: cnt = census(cid)[0]
    except Exception: return cid, []
    hs = sorted([(c, h) for h, c in cnt.items() if int(h, 16) & 0x3fff == 0x20cc], reverse=True)[:40]
    for c, h in hs:
        try:
            ok, v, _ = ecall(u, {'to': h, 'data': sel('VERSION()')})
            ok2, p, _ = ecall(u, {'to': h, 'data': sel('pendingClaims(address)') + adr('0x' + '0' * 40)})
            ok3, f, _ = ecall(u, {'to': h, 'data': sel('factory()')})
            out.append((h, c, s(v) if ok else None, ok2, f[-40:] if ok3 else None))
        except Exception as e: out.append((h, c, 'err ' + repr(e)[:40], None, None))
    return cid, out
with cf.ThreadPoolExecutor(8) as ex:
    for cid, out in ex.map(one, [n['chainId'] for n in NETS]):
        for o in out:
            if o[2] or o[3]: print(cid, *o)
