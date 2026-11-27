"""Cycle 29 stablecoin-l1, lead L-1179: the 23 multi-transaction scenarios of
cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py sent to a JSON-RPC endpoint as one eth_simulateV1
block (state carried from call to call, transient storage cleared between calls because each call is its own transaction),
with the PoolManager build of this checkout, the cycle 25 driver and the token doubles placed by state override.
Each call's status and return bytes are compared with tools/opdiff/pyevm.py (scen28.ref). Read-only.
Usage: python3 scen_rpc.py <out.json> <url> [time_override_unix] [names...]"""
import sys, os, json
S28 = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '028',
                                   'theme-monad-native-unentered-blocks.work', 'scripts'))
sys.path.insert(0, S28)
import scen28 as X  # noqa: E402
from evm import rpc  # noqa: E402
BLOCK_GAS = int(os.environ.get('BLOCK_GAS', '0'))
CALLMANY = os.environ.get('CALLMANY') == '1'


def main():
    out, url = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    t_over = None
    if rest and rest[0].isdigit():
        t_over = int(rest[0]); rest = rest[1:]
    names = rest or list(X.SCEN)
    res = {'url': url, 'timeOverride': t_over, 'clientBefore': rpc(url, 'web3_clientVersion', [], 20),
           'block': int(rpc(url, 'eth_blockNumber', [], 20), 16), 'scenarios': {}}
    tot = {'calls': 0, 'equal': 0, 'diff': 0, 'err': 0}
    for nm in names:
        sc = X.SCEN[nm]
        ref_outs, _ = X.ref(sc)
        cs = X.codes_for(X.PM, [sc['key']])
        cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
        so = {'0x%040x' % a: {'code': '0x' + b.hex()} for a, b in cs.items()}
        if sc['storage']:
            so['0x%040x' % X.PM]['stateDiff'] = {'0x%064x' % int(k, 16): '0x%064x' % int(v, 16) for k, v in sc['storage'].items()}
        n = len(sc['txs'])
        if BLOCK_GAS:
            g = (BLOCK_GAS - 1000) // n; bo = {'gasLimit': hex(BLOCK_GAS)}
        else:
            g = min(45_000_000, 400_000_000 // n); bo = {'gasLimit': hex(g * n + 1)}
        calls = [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % X.addr(t['to']), 'data': '0x' + t['data'],
                  'gas': hex(g)} for t in sc['txs']]
        if t_over: bo['time'] = hex(t_over)
        r = {'ntx': n, 'gasPerCall': g, 'method': 'eth_callMany' if CALLMANY else 'eth_simulateV1'}
        try:
            if CALLMANY:
                if n > 10: raise RuntimeError('skipped: more than the 10 calls eth_callMany accepts on this endpoint')
                cm = rpc(url, 'eth_callMany', [[{'transactions': calls}], {'blockNumber': 'latest'}, so], timeout=180)
                got = []
                for x in cm[0]:
                    if x.get('error') is None: got.append({'status': '0x1', 'returnData': x.get('value') or '0x'})
                    else:
                        e = str(x['error']); hx = e.split('0x')[-1] if '0x' in e else ''
                        got.append({'status': '0x0', 'returnData': '0x' + hx.strip(), 'error': {'message': e[:200]}})
            else:
                sim = rpc(url, 'eth_simulateV1', [{'blockStateCalls': [{'blockOverrides': bo, 'stateOverrides': so, 'calls': calls}],
                                                  'validation': False}, 'latest'], timeout=180)
                got = sim[0]['calls']
            per = []
            for i, ((rok, rret), g) in enumerate(zip(ref_outs, got)):
                eok = g.get('status') == '0x1'
                eret = (g.get('returnData') or '0x')[2:]
                if not eok and not eret and isinstance(g.get('error'), dict):
                    eret = (g['error'].get('data') or '0x')[2:]
                same = (rok == eok) and (rret == eret)
                per.append({'i': i, 'refOk': rok, 'ok': eok, 'same': same, 'gasUsed': g.get('gasUsed'),
                            'err': (g.get('error') or {}).get('message') if not same else None,
                            'ref': rret[:200] if not same else None, 'got': eret[:200] if not same else None})
                tot['calls'] += 1; tot['equal' if same else 'diff'] += 1
            r['calls'] = per; r['allSame'] = all(p['same'] for p in per) and len(got) == len(ref_outs)
        except Exception as e:  # noqa
            r['error'] = str(e)[:400]; tot['err'] += 1
        res['scenarios'][nm] = r
        print(nm, r.get('allSame'), r.get('error', '')[:200] if 'error' in r else
              [p['i'] for p in r['calls'] if not p['same']], flush=True)
    res['clientAfter'] = rpc(url, 'web3_clientVersion', [], 20); res['totals'] = tot
    print('TOTAL', tot, flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
