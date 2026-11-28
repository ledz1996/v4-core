"""Cycle 39 (L-1356): repeat the 30M and 20M probes of gasprobe.py N times on one endpoint, with web3_clientVersion
after each call, to see whether answers depend on the backend. usage: python3 gasprobe2.py out.json url N"""
import json, sys, importlib.util, os
spec = importlib.util.spec_from_file_location('gp', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gasprobe.py'))
src = open(spec.origin).read(); src = src[:src.index('out = {}')]
g = {}; exec(src, g)
url, N = sys.argv[2], int(sys.argv[3]); rows = []
for i in range(N):
    for gas in (20_000_000, 30_000_000):
        row = {'i': i, 'gas': gas}
        for name, code in (('p_gas', g['ret_gas']), ('p_call', g['caller'](g['CHILD'])), ('p_sstore', g['caller'](g['CHILD2']))):
            ov = {g['P']: {'code': '0x' + code}, g['CHILD']: {'code': '0x' + g['ret_gas']}, g['CHILD2']: {'code': '0x' + g['sstore_then_gas']}}
            r = g['rpc'](url, 'eth_call', [{'from': '0x' + '00' * 19 + '01', 'to': g['P'], 'gas': hex(gas)}, 'latest', ov])
            row[name] = int(r['result'], 16) if 'result' in r else r.get('error')
            row[name + '_cv'] = g['rpc'](url, 'web3_clientVersion', [])['result']
        rows.append(row); print(row, flush=True)
json.dump({'url': url, 'rows': rows}, open(sys.argv[1], 'w'), indent=1)
