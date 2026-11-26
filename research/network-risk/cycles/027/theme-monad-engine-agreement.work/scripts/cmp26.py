"""Classify fixed-harness results of the cycle 26 cases against the pyevm reference words (ref-143.json of cycle 26,
pyevm26.py run per case at the Monad PoolManager address). Classes: EQ (every word equal); TOKMODEL (the only differing
words are the driver's ERC-20 balance reads, where the harness token gives the driver 2^250 and the reference token mints
on demand, and the token is conserved: driver + PoolManager + hook + S end balances = the driver's start balance, 2^246 as the harness parses the odd-length hex 2^250); PRECOMPILE (native take to
a precompile address, which the harness answers as an account without code); OTHER. Usage: cmp26.py <hx-results.json> <out.json>"""
import sys, json, os
C26 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '026', 'theme-hook-and-native-sides.work')
R = json.load(open(os.path.join(C26, 'out', 'ref-143.json')))['results']
cases = {str(c['id']): c for c in json.load(open(os.path.join(C26, 'out', 'cases.json')))['cases']}
res = json.load(open(sys.argv[1]))['results']
out = {}
HXBAL = 1 << 246  # hxrun26 writes 2^250 as 63 hex digits; the harness reads whole byte pairs and keeps 0x40 << 240
for v, rr in res.items():
    cl = {}
    for k, x in rr.items():
        a, b, f = x['interp'], x['native'], R[k]
        eng = 'SAME' if x['same'] else 'DIFF'
        if a.get('ok') != f.get('ok') or a.get('revert') != f.get('revert') or (a.get('w') is None) != (f.get('w') is None):
            cl[k] = {'engines': eng, 'ref': 'NE', 'class': 'OTHER', 'why': 'ok/revert/shape'}; continue
        if a.get('w') == f.get('w'):
            cl[k] = {'engines': eng, 'ref': 'EQ', 'class': 'EQ'}; continue
        hw = [int(t, 16) for t in a['w']]; fw = [int(t, 16) for t in f['w']]; n = len(hw)
        diff = [i for i in range(n) if hw[i] != fw[i]]
        c = cases[k]; toks = [j for j, t in enumerate((c.get('t0'), c.get('t1'))) if t]
        dpos = set()
        for j in toks: dpos |= {2 + j, n - 8 + 2 + j}
        tag = c['tag']
        if set(diff) <= dpos:
            cons = all(hw[n - 8 + 2 + j] + hw[n - 8 + j] + hw[n - 8 + 4 + j] + hw[n - 8 + 6 + j] == hw[2 + j] and hw[2 + j] == HXBAL for j in toks)
            cl[k] = {'engines': eng, 'ref': 'EQ-masked' if cons else 'NE', 'class': 'TOKMODEL' if cons else 'OTHER', 'diff': diff}
        elif 'precompile' in tag:
            cl[k] = {'engines': eng, 'ref': 'NE', 'class': 'PRECOMPILE', 'diff': diff, 'tag': tag}
        else:
            cl[k] = {'engines': eng, 'ref': 'NE', 'class': 'OTHER', 'diff': diff, 'tag': tag}
    from collections import Counter
    out[v] = {'summary': dict(Counter((x['engines'], x['class']) and f"{x['engines']}/{x['class']}" for x in cl.values())), 'cases': cl}
    print(v, out[v]['summary'], [k for k, x in cl.items() if x['class'] == 'OTHER'][:20])
json.dump(out, open(sys.argv[2], 'w'), indent=0)
