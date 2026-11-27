"""Merge census state files (disjoint block sets) into out/census-summary.json and map PoolManager sites to src/ lines.
Usage: agg.py <state json> [...]"""
import json, sys, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPN = {2: 'MUL', 4: 'DIV', 5: 'SDIV', 6: 'MOD', 7: 'SMOD', 8: 'ADDMOD', 9: 'MULMOD', 10: 'EXP', 11: 'SIGNEXTEND', 18: 'SLT', 19: 'SGT',
       26: 'BYTE', 27: 'SHL', 28: 'SHR', 29: 'SAR', 32: 'KECCAK256', 85: 'SSTORE', 87: 'JUMPI', 92: 'TLOAD', 93: 'TSTORE', 94: 'MCOPY'}
CL = {(2, 1): 'product >= 2^256', (4, 1): 'by zero', (6, 1): 'by zero', (5, 1): 'negative dividend', (5, 2): 'negative divisor',
      (5, 3): 'by zero', (5, 4): '-2^255 by -1', (7, 1): 'negative dividend', (7, 2): 'negative divisor', (7, 3): 'by zero',
      (8, 1): 'sum >= 2^256', (8, 2): 'modulus 2^256-1', (8, 3): 'modulus 0', (9, 1): 'modulus 2^256-1, product >= 2^256',
      (9, 2): 'other nonzero modulus, product >= 2^256', (9, 3): 'modulus 0', (9, 4): 'modulus >= 2^192 (not 2^256-1), product >= 2^256',
      (9, 5): 'modulus < 2^128, product >= 2^256', (10, 1): 'exponent >= 256',
      (11, 1): 'byte 0-2, sign set', (11, 2): 'byte 3-30, sign set', (11, 3): 'index >= 31', (11, 4): 'byte 0-2, sign clear, dirty high bits',
      (11, 5): 'byte 0-2, sign set, high bits not all ones', (18, 1): 'different sign', (18, 2): 'both negative', (19, 1): 'different sign',
      (19, 2): 'both negative', (26, 1): 'index < 32', (26, 2): 'index >= 32', (26, 3): 'index 0', (26, 4): 'index 31',
      (27, 1): 'shift >= 256', (27, 2): 'shift 0', (27, 3): 'shift 1-255', (28, 1): 'shift >= 256', (28, 2): 'shift 0', (28, 3): 'shift 1-255',
      (29, 1): 'negative value, shift < 256', (29, 2): 'negative value, shift >= 256', (29, 3): 'non-negative value, shift >= 256',
      (32, 1): 'length 64', (32, 2): 'length 58', (32, 3): 'length 160', (32, 4): 'length 136 (one rate block)', (32, 5): 'length 135 or 137',
      (32, 6): 'length 0', (32, 7): 'length 32', (32, 8): 'length > 136 (two or more blocks)', (32, 9): 'other length',
      (85, 1): 'restores the value at transaction start', (85, 2): 'writes the current value again', (85, 9): 'current value unreadable',
      (87, 1): 'condition zero', (87, 2): 'condition nonzero >= 2^64', (87, 3): 'condition nonzero < 2^64',
      (94, 1): 'overlap, destination above source', (94, 2): 'overlap, destination below or equal source'}
for k in range(1, 5): CL[(4, 10 + k)] = 'dividend >= 2^192, divisor of %d limbs' % k; CL[(9, 10 + k)] = 'product >= 2^256, modulus of %d limbs (not 2^256-1)' % k
for i in range(31):
    for b in (0, 1): CL[(11, 100 + 2 * i + b)] = 'byte %d, sign %s' % (i, 'set' if b else 'clear')


def name(op, cl):
    return OPN.get(op, str(op)) + ' ' + ('executed' if cl == 0 else CL.get((op, cl), str(cl)))


cls, pm, hdr, brackets, failed, txs, pmb = {}, {}, {}, [], {}, 0, []
for f in sys.argv[1:]:
    s = json.load(open(f))
    for b in s['hdr']:
        if b in hdr: raise SystemExit('overlap ' + b + ' ' + f)
    hdr.update(s['hdr']); brackets += s['brackets']; failed.update(s['failed']); txs += s['txs']; pmb += s['pmBlocks']
    for k, e in s['cls'].items():
        c = cls.get(k)
        if c is None: cls[k] = dict(e); continue
        c['occ'] += e['occ']; c['blocks'] += e['blocks']; c['txs'] += e['txs']
        if e['first'] < c['first']: c['first'], c['firstEx'] = e['first'], e['firstEx']
        if e['last'] > c['last']: c['last'], c['lastEx'] = e['last'], e['lastEx']
    for k, e in s['pm'].items():
        c = pm.get(k)
        if c is None: pm[k] = dict(e); continue
        c['occ'] += e['occ']; c['first'] = min(c['first'], e['first'])
        if e['last'] >= c['last']: c.update({x: e[x] for x in ('last', 'tx', 'a', 'b', 'c')})
inv = json.load(open(os.path.join(W, 'out', 'pm-inventory.json')))
sites = []
for x in inv:
    pc = x['pc']; seen = {}
    for k, e in pm.items():
        op, cl, p = map(int, k.split(':'))
        if p == pc: seen[name(op, cl)] = [e['occ'], e['first'], e['last'], e['tx']]
    sites.append({'pc': pc, 'op': x['op'], 'src': '%s:%s' % (x['src'].get('file'), x['src'].get('line')), 'snippet': x['src'].get('snippet', '')[:80], 'shapes': seen})
bns = sorted(int(b) for b in hdr)
out = {'blocks': len(bns), 'firstBlock': bns[0], 'lastBlock': bns[-1], 'txs': txs, 'blocksWithFailedTxTrace': len(failed), 'failedExamples': dict(list(failed.items())[:20]),
       'pmBlocks': len(set(pmb)), 'clientVersions': sorted({b['before'] for b in brackets} | {b['after'] for b in brackets}), 'chunks': len(brackets),
       'shapes': {name(*map(int, k.split(':'))): {x: v for x, v in e.items() if x != '_lb'} for k, e in sorted(cls.items(), key=lambda kv: tuple(map(int, kv[0].split(':'))))},
       'pmSites': sites}
json.dump(out, open(os.path.join(W, 'out', os.environ.get('OUT', 'census-summary.json')), 'w'), indent=1)
print(out['blocks'], out['firstBlock'], out['lastBlock'], txs, len(failed), out['pmBlocks'], out['clientVersions'])
for k, e in out['shapes'].items(): print('%-70s %10d %7d %9d %9d' % (k, e['occ'], e['blocks'], e['first'], e['last']))
