# Chains without full Initialize discovery: read the aToken list from the Aave v3 Pool on chain and read the PoolManager's
# balance of each at B1 and B2 of the main run, plus a short list of other candidates. Read-only.
import sys, json
from lib import *
from config import CFG
from reconcile import mc
def run(cid, pool, extra=()):
    o = jl('raw/reconcile_%d.json' % cid); pm = o['poolManager']; su = CFG[cid]['state']
    lst = call(su[0], pool, 'getReservesList()'); b = bytes.fromhex(lst[2:]); n = int.from_bytes(b[32:64], 'big')
    assets = ['0x' + b[64 + 32 * i + 12:64 + 32 * i + 32].hex() for i in range(n)]
    rd = mc(su, [(pool, sel('getReserveData(address)') + adr(a)) for a in assets], o['B2'], size=20, ts=o['t2'])
    toks = []
    for a, x in zip(assets, rd):
        if x and x[0] and len(x[1]) >= 32 * 9: toks.append('0x' + x[1][32 * 8 + 12:32 * 9].hex())
    toks += [e.lower() for e in extra]
    data = '0x70a08231' + adr(pm)
    r1 = mc(su, [(t, data) for t in toks], o['B1'], ts=o['t1']); r2 = mc(su, [(t, data) for t in toks], o['B2'], ts=o['t2'])
    sy = mc(su, [(t, '0x95d89b41') for t in toks], o['B2'], ts=o['t2'])
    known = {r['token']: r for r in o['rows']}
    rows = []
    for t, a, b_, s in zip(toks, r1, r2, sy):
        g = lambda x: int.from_bytes(x[1][:32], 'big') if x and x[0] and len(x[1]) >= 32 else None
        name = s[1][64:64 + int.from_bytes(s[1][32:64], 'big')].decode('utf8', 'replace') if s and s[0] and len(s[1]) >= 64 else '?'
        x1, x2 = g(a), g(b_)
        if x1 or x2:
            k = known.get(t)
            rows.append(dict(token=t, symbol=name, bal1=str(x1), bal2=str(x2), change=str((x2 or 0) - (x1 or 0)), inMainRun=bool(k), mainRunStatus=(k or {}).get('status'), tin=(k or {}).get('tin', '0'), tout=(k or {}).get('tout', '0')))
    json.dump(dict(chainId=cid, pool=pool, reserves=n, B1=o['B1'], B2=o['B2'], rows=rows), open('raw/aave_targets_%d.json' % cid, 'w'), indent=1)
    print(cid, 'reserves', n, 'tokens with PoolManager balance', len(rows))
    for r in rows: print('  ', r['token'], r['symbol'], r['bal1'], r['bal2'], 'change', r['change'], 'in main run', r['inMainRun'], r['mainRunStatus'])
if __name__ == '__main__':
    run(8453, '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5', ['0xB79DD08EA68A908A97220C76d19A6aA9cBDE4376', '0xDBFeFD2e8460a6Ee4955A68582F85708BAEA60A3', '0xb125E6687d4313864e53df431d5425969c15Eb2F', '0x46e6b214b524310239732D51387075E0e70970bf', '0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf'])
