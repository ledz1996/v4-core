# Token symbol/decimals for exposed claim ids and a rough dollar figure for majors (stable = 1, ETH 1700, BTC 60900; prices as shown by Blockscout holdings pages read in cycle 4).
import sys, json, os
from lib import *
from state import url, bcall
from exposure import load
NATIVE = {1: ('ETH', 1700), 10: ('ETH', 1700), 8453: ('ETH', 1700), 130: ('ETH', 1700), 7777777: ('ETH', 1700), 480: ('ETH', 1700), 57073: ('ETH', 1700), 1868: ('ETH', 1700), 42220: ('CELO', 0.1), 196: ('OKB', 60), 42161: ('ETH', 1700), 4663: ('ETH', 1700), 99901: ('HYPE', 60), 137: ('POL', 0.1), 56: ('BNB', 600), 43114: ('AVAX', 10), 143: ('MON', 0.02), 4326: ('ETH', 1700), 4217: ('-', 0), 5042: ('USDC', 1), 999: ('HYPE', 60)}
def price(sym):
    s = (sym or '').upper().replace('₮', 'T')
    if s in ('USDC', 'USDT', 'DAI', 'USDT0', 'USD₮0', 'USDC.E', 'USDE', 'USDS', 'PYUSD', 'USD1', 'USDG', 'GHO', 'USDTB', 'FRAX', 'CRVUSD', 'RLUSD', 'USDBC', 'AUSD', 'EURC', 'PATHUSD'): return 1
    if s in ('WETH', 'ETH', 'WSTETH', 'STETH', 'CBETH', 'WEETH', 'RETH'): return 1700
    if s in ('WBTC', 'CBBTC', 'TBTC', 'BTCB', 'KBTC', 'LBTC'): return 60900
    return None
def dec_str(h):
    try:
        b = bytes.fromhex(h[2:])
        if len(b) >= 96: n = int.from_bytes(b[32:64], 'big'); return b[64:64 + n].decode('utf8', 'replace')
        return b.rstrip(b'\0').decode('utf8', 'replace')
    except Exception: return None
def run(cid):
    rows = load(cid); u = url(cid)
    ids = sorted({i for r in rows for m in r['exposed'].values() for i in m})
    toks = ['0x' + i[-40:] for i in ids]
    r1 = bcall(u, [('eth_call', [{'to': t, 'data': '0x95d89b41'}, 'latest']) for t in toks])
    r2 = bcall(u, [('eth_call', [{'to': t, 'data': '0x313ce567'}, 'latest']) for t in toks])
    meta = {}
    for i, t, s, d in zip(ids, toks, r1, r2):
        if int(t, 16) == 0: meta[i] = dict(sym=NATIVE[cid][0], dec=18, px=NATIVE[cid][1]); continue
        sym = dec_str(s) if isinstance(s, str) else None
        try: dec = int(d, 16) if isinstance(d, str) and len(d) > 2 else None
        except Exception: dec = None
        if dec is not None and dec > 77: dec = None
        meta[i] = dict(sym=sym, dec=dec, px=price(sym))
    out = []
    for r in rows:
        usd = 0; items = []
        for o, m in r['exposed'].items():
            for i, a in m.items():
                mt = meta[i]; v = (a / 10 ** mt['dec'] * mt['px']) if (mt['px'] is not None and mt['dec'] is not None) else None
                if v: usd += v
                items.append([o, '0x' + i[-40:], mt['sym'], mt['dec'], str(a), v])
        out.append(dict(x=r['x'], kind=r['kind'], nOp=r['nOp'], nAl=r['nAl'], owners=len(r['exposed']), ownerCode=r['ownerCode'], usdMajors=usd, items=items))
    json.dump(out, open(os.path.join(HERE, 'raw', 'exposure_%d.json' % cid), 'w'))
    return out
if __name__ == '__main__':
    for c in sys.argv[1:]:
        cid = int(c); out = run(cid)
        print('==', cid, net(cid)['name'], 'approved', len(out), 'exposed', sum(1 for r in out if r['owners']), 'usd in majors %.0f' % sum(r['usdMajors'] for r in out))
        for r in sorted(out, key=lambda r: -r['usdMajors'])[:25]:
            if not r['owners']: continue
            top = sorted([it for it in r['items']], key=lambda it: -(it[5] or 0))[:3]
            print('  %s %-34s op %2d al %3d owners %3d usd %12.0f | %s' % (r['x'], r['kind'][:34], r['nOp'], r['nAl'], r['owners'], r['usdMajors'], '; '.join('%s %s %.4g' % (it[0][:8], it[2], int(it[4]) / 10 ** (it[3] or 0)) for it in top)))
