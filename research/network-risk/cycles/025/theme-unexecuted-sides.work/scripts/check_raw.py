"""Exact relations for the 28 raw 'deposit ts=32767' swaps (kind 7: init at 2^96, L = 2^100 over [-23*32767, 27*32767],
one swap) and the step flags of the ERC-6909 sequences. Usage: python3 check_raw.py <allcases.json> <results.json> <out.json>"""
import sys, os, json
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v4math as V, check as C
cs = {c['id']: c for c in json.load(open(sys.argv[1]))['cases']}; ref = json.load(open(sys.argv[2]))['results']
Q96 = 1 << 96; rows = []
for cid, c in cs.items():
    if not c['tag'].startswith('deposit ts=32767'): continue
    W = [int(x, 16) for x in ref[str(cid)]['w']]
    if W[6] != 1: rows.append({'id': cid, 'tag': c['tag'], 'status': 'swap reverted', 'sel': hex(W[7] >> 224)}); continue
    d0, d1 = C.unpack(W[7]); s1 = W[11] & ((1 << 160) - 1); s0 = 1 << 96; L = 1 << 100
    pl, pu = V.get_sqrt_price_at_tick(-23 * 32767), V.get_sqrt_price_at_tick(27 * 32767)
    lo, hi = max(min(s0, s1), pl), min(max(s0, s1), pu)
    A0 = F(L * Q96 * (hi - lo), lo * hi); A1 = F(L * (hi - lo), Q96); f = c['fee']; zfo = c['tag'].split()[4] == 'zfo'
    g, o, Ai, Ao = (-d0, d1, A0, A1) if zfo else (-d1, d0, A1, A0)
    v = []
    if g * (10 ** 6 - f) < Ai * 10 ** 6: v.append('input below exact plus fee')
    if o > Ao or o < 0: v.append('output above exact')
    rows.append({'id': cid, 'tag': c['tag'], 'status': 'ok', 'gross': g, 'out': o, 'violations': v})
names = ['mint', 'transfer x', 'transfer above balance', 'approve fin', 'S transferFrom y', 'allowance', 'S transferFrom fin (above allowance)',
         'approve max', 'S transferFrom y (max)', 'allowance', 'approve 0', 'setOperator', 'S transferFrom y (operator)', 'allowance',
         'S burn z (operator)', 'delta S', 'S take z', 'setOperator false', 'approve w', 'S burn w (allowance)', 'allowance', 'S take w',
         'S burn 1 (no allowance)', 'S transferFrom 1 (no allowance)', 'burn own']
e = {}
for cid in (1369, 1370, 1371):
    W = [int(x, 16) for x in ref[str(cid)]['w']]; i = 0; out = []
    for n in names:
        if n in ('allowance', 'delta S'): out.append([n, W[i]]); i += 1
        else: out.append([n, W[i], hex(W[i + 1] >> 224) if not W[i] else '']); i += 3
    e[cs[cid]['tag']] = out
json.dump({'depositSwaps': rows, 'violations': sum(1 for r in rows if r.get('violations')), 'erc6909Steps': e}, open(sys.argv[3], 'w'), indent=0, default=str)
print(len(rows), sum(1 for r in rows if r['status'] == 'ok'), 'violations', sum(1 for r in rows if r.get('violations')))
