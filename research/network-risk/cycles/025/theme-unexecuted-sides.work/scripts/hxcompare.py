"""Compare the Monad harness words (interpreter and native, v0.16.5 and v0.16.7) with the reference EVM words.
The harness driver is pre-funded with 2^250 of each token and transfers instead of minting, so the two words that
hold the driver's own token balances differ by construction; every other word must be equal.
Usage: python3 hxcompare.py <hx-results.json> <ref.json> <allcases.json> <out.json>"""
import sys, json
hx = json.load(open(sys.argv[1])); ref = json.load(open(sys.argv[2]))['results']
kinds = {str(c['id']): c['kind'] for c in json.load(open(sys.argv[3]))['cases']}
DPOS = {0: (-2, -1), 1: (-2, -1), 5: (-2, -1), 2: (-2, -1), 3: (-3, -2), 4: (-3, -2), 7: (-2, -1)}
out = {}
for ver, rs in hx.items():
    eq = dif = 0; rows = []
    for k, x in rs.items():
        r = ref[str(k)]
        for eng in ('interp', 'native'):
            e = x.get(eng)
            if e is None: rows.append({'case': k, 'engine': eng, 'why': 'no output'}); dif += 1; continue
            if r.get('ok') != e.get('ok'): rows.append({'case': k, 'engine': eng, 'why': 'unlock ok differs', 'hx': e, 'ref': r}); dif += 1; continue
            if not r.get('ok'):
                if r.get('revert') == e.get('revert'): eq += 1
                else: rows.append({'case': k, 'engine': eng, 'why': 'revert data differs', 'hx': e.get('revert'), 'ref': r.get('revert')}); dif += 1
                continue
            a, b = r['w'], e['w']
            skip = {len(a) + p for p in DPOS[kinds[str(k)]]}
            bad = [i for i in range(max(len(a), len(b))) if i not in skip and (i >= len(a) or i >= len(b) or a[i] != b[i])]
            if bad: rows.append({'case': k, 'engine': eng, 'why': 'words differ', 'positions': bad[:10]}); dif += 1
            else: eq += 1
    out[ver] = {'equal': eq, 'different': dif, 'rows': rows}
    print(ver, 'equal', eq, 'different', dif, [ (x['case'], x['engine'], x['why']) for x in rows][:12])
json.dump(out, open(sys.argv[4], 'w'), indent=0)
