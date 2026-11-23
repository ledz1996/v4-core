# Add name, symbol, decimals and totalSupply to every row that did not reconcile and write raw/mismatch_<cid>.json.
import sys, json, glob, os
from lib import *
from config import CFG
from reconcile import mc
def dstr(b):
    try:
        if len(b) >= 64 and int.from_bytes(b[:32], 'big') == 32:
            n = int.from_bytes(b[32:64], 'big'); return b[64:64 + n].decode('utf8', 'replace')
        return b[:32].rstrip(b'\0').decode('utf8', 'replace')
    except Exception: return '?'
def run(cid, tag=''):
    fn = 'raw/reconcile_%d%s.json' % (cid, tag)
    if not (os.path.exists(fn) or os.path.exists(fn + '.gz')): return
    o = jl(fn); ms = [r for r in o['rows'] if r['status'] in ('mismatch', 'unreadable')]
    toks = [r['token'] for r in ms]; calls = []
    for t in toks: calls += [(t, '0x06fdde03'), (t, '0x95d89b41'), (t, '0x313ce567'), (t, '0x18160ddd')]
    res = mc(o['stateUrl'], calls, o['B2'], size=200, ts=o['t2']) if calls else []
    for i, r in enumerate(ms):
        a = res[4 * i:4 * i + 4]
        g = lambda x: x[1] if x and x[0] else b''
        r['name'] = dstr(g(a[0])); r['symbol'] = dstr(g(a[1]))
        r['decimals'] = int.from_bytes(g(a[2])[:32], 'big') if g(a[2]) else None
        r['totalSupply'] = str(int.from_bytes(g(a[3])[:32], 'big')) if g(a[3]) else None
    json.dump(dict(chainId=cid, name=o['name'], B1=o['B1'], B2=o['B2'], seconds=o['seconds'], counts=o['counts'], universe=o['universe'], rows=ms), open('raw/mismatch_%d%s.json' % (cid, tag), 'w'), indent=1)
    print('==', cid, o['name'], 'B1', o['B1'], 'B2', o['B2'], o['seconds'], 's', o['counts'], 'universe', o['universe'])
    for r in sorted(ms, key=lambda r: r['status']):
        if r['status'] == 'unreadable': print('  UNREAD', r['token'], r['symbol'], r['bal1'], r['bal2'], r['nlogs']); continue
        d = r['decimals'] or 0; b2 = int(r['bal2']); b1 = int(r['bal1']); df = int(r['diff'])
        ts = int(r['totalSupply']) if r['totalSupply'] else 0
        print('  %s %-12s dec=%-2s bal2=%.6g diff=%+.6g (%.3g%% of bal1) logs=%d in=%.4g out=%.4g share=%.3g%%' % (r['token'], (r['symbol'] or '')[:12], d, b2 / 10 ** d, df / 10 ** d, 100 * df / b1 if b1 else float('nan'), r['nlogs'], int(r['tin']) / 10 ** d, int(r['tout']) / 10 ** d, 100 * b2 / ts if ts else float('nan')))
if __name__ == '__main__':
    for a in sys.argv[1:]: run(int(a))
