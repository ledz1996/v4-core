import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
NZ = keccak(b'NonzeroNativeValue()')[:4].hex()
r = json.load(open(sys.argv[1])); summary = {}
def iv(h): return int(h[:64], 16) if h else None
def sgn(x): return x - 2**256 if x is not None and x >= 2**255 else x
for cid, n in r.items():
    out = []
    for c in n['cases']:
        if 'steps' not in c: out.append({'case': c['case'], 'verdict': 'not run', 'why': str(c.get('skipped') or c.get('raw'))[:160]}); continue
        L = {s['label']: s for s in c['steps']}
        g = lambda l: (L[l]['ok'] if L[l]['ret'] == '' and l.startswith(('PM native', 'forced')) else iv(L[l]['ret'])) if l in L else None
        ok = lambda l: L[l]['ok'] if l in L else None
        d = {'case': c['case']}
        if c['case'].startswith('native forced'):
            d.update(inflow=g('PM native after inflow') - g('PM native before'), paid=g('settle() value 0'), delta=sgn(g('delta(driver,native)')), createOk=g('forced native inflow (selfdestruct)') != 0)
            d['verdict'] = 'nothing' if d['paid'] == 0 and d['delta'] == 0 and d['inflow'] == 10**6 else 'CHECK'
        elif c['case'].startswith('native take'):
            x = 1000 if cid != '4217' else None
            d.update(takeOk=ok('take native x'), drop=(g('PM native before') - g('PM native after take')) if ok('take native x') else None, paid=g('settle() value x'), back=g('PM native after settle') - g('PM native before'), delta=sgn(g('delta(driver,native)')))
            d['verdict'] = 'exact' if d['takeOk'] and d['drop'] == 1000 and d['paid'] == 1000 and d['back'] == 0 and d['delta'] == 0 else ('take reverts' if not d['takeOk'] else 'CHECK')
        elif c['case'].startswith('token round trip'):
            x = c['x']; tk = ok('take(T,driver,x)')
            d.update(x=x, takeOk=tk, drop=(g('balanceOf(PM) before') - g('balanceOf(PM) after take')) if tk else None, got=g('balanceOf(driver) after take') if tk else None,
                     nativeDrop=g('PM native before') - g('PM native after take'), repayOk=ok('driver T.transfer(PM,x)'), back=(g('balanceOf(PM) after repay') - g('balanceOf(PM) before')) if tk else None,
                     settleOk=ok('settle()'), paid=g('settle()') if ok('settle()') else None, delta=sgn(g('delta(driver,T)')))
            if not tk: d['verdict'] = 'take reverts'; d['takeRet'] = L['take(T,driver,x)']['ret'][:200]
            elif d['drop'] == x and d['got'] == x and d['back'] == 0 and d['paid'] == x and d['delta'] == 0: d['verdict'] = 'exact'
            else: d['verdict'] = 'CHECK'
        elif c['case'].startswith('face forced'):
            fb, fa = g('face balanceOf(PM) before'), g('face balanceOf(PM) after inflow')
            last = L['settle() value 1 with face synced']
            d.update(faceRise=(fa - fb) if fa is not None and fb is not None else None, faceBeforeOk=ok('face balanceOf(PM) before'), syncOk=ok('sync(face)'), paid=g('settle() value 0') if ok('settle() value 0') else None,
                     settleRet=L['settle() value 0']['ret'][:80], deltaFace=sgn(g('delta(driver,face)')), deltaNative=sgn(g('delta(driver,native)')),
                     valueSettleReverts=last['ok'] == 0, valueSettleSel=last['ret'][:8], nz=last['ret'][:8] == NZ)
            if d['syncOk'] and d['paid'] is not None and d['paid'] == d['faceRise'] == d['deltaFace'] and d['deltaNative'] == 0: d['verdict'] = 'self-paid credit only'
            elif not d['syncOk'] or not d['faceBeforeOk']: d['verdict'] = 'face balanceOf reverts'
            else: d['verdict'] = 'CHECK'
        out.append(d)
    summary[cid] = {'name': n['name'], 'block': n['blockNumber'], 'client': [(n['before'].get('web3_clientVersion') or {}).get('result'), (n['after'].get('web3_clientVersion') or {}).get('result')], 'cases': out}
json.dump(summary, open(sys.argv[2], 'w'), indent=1)
for cid, s in summary.items():
    print(cid, s['name'], s['block'], s['client'])
    for d in s['cases']: print('   ', d['verdict'], '|', {k: v for k, v in d.items() if k not in ('verdict',)})
