# Shared helpers for theme-transfer-side-effects (cycle 7). Read-only JSON-RPC only. Builds on the cycle 5 and 6 helpers.
import os, sys, json, gzip, time
HERE7 = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.join(HERE7, '..', '..', '005', 'theme-assigned-balance.work')
W6C = os.path.join(HERE7, '..', '..', '006', 'theme-currency-lists.work')
W6T = os.path.join(HERE7, '..', '..', '006', 'theme-token-triggers.work')
sys.path.insert(0, W5)
from common import post, rpc, batch, sel, u256, adr, NETS, net, urls2, ecall, EXTRA
from asm import assemble, MULTI, FWD, FWDN, OPS, _bal, _xfer
from abi import split_types, encode, supported
RAW5 = os.path.join(W5, 'raw'); RAW6C = os.path.join(W6C, 'raw'); RAW6T = os.path.join(W6T, 'raw')
RAW7 = os.path.join(HERE7, 'raw')
A = '0x00000000000000000000000000000000000a11ce'; SINK = '0x00000000000000000000000000000000005111c0'
MC3 = '0xca11bde05977b3631167028862be2a173976ca11'
def jz(fn): return json.load(gzip.open(fn, 'rt'))
def wz(fn, o): json.dump(o, gzip.open(fn, 'wt'))
def prices(cid):
    """token -> price record, union of every price list of cycles 5 and 6."""
    out = {}
    for fn in (os.path.join(RAW5, 'prices_%d.json.gz' % cid), os.path.join(RAW6C, 'prices_%d.json.gz' % cid)):
        if os.path.exists(fn):
            for t, p in jz(fn).items(): out.setdefault(t.lower(), p)
    for f in ('prices3_%d.json.gz', 'pricesall_%d.json.gz'):
        fn = os.path.join(RAW6T, f % cid)
        if os.path.exists(fn):
            d = jz(fn)
            for t, p in (d.get('llama') or d.get('prices') or {}).items(): out.setdefault(t.lower(), p)
            for t, p in (d.get('gecko') or {}).items():
                if p.get('price') is not None and p.get('decimals') is not None: out.setdefault(t.lower(), p)
    return {t: p for t, p in out.items() if p.get('price') is not None and p.get('decimals') is not None and int(t, 16) != 0}
def usdv(b, p):
    try: return b / 10 ** int(p['decimals']) * float(p['price'])
    except Exception: return 0.0
CIDS = [n['chainId'] for n in NETS]
