"""Task 4: check results against rules that do not come from src/.
Usage: python3 task4.py <cases.json> <result file (ref or chain)> <out.json>

R1 conservation: when unlock succeeds, for each currency the rise of the PoolManager's balance equals what the three
   actors (driver, hook, S) paid in less what they took out, read from the token double or native balances:
   PM rise == -(rise of D + H + S balances) for token currencies, where only the driver mints and only to the PoolManager,
   so PM rise + actors' rise == amount minted; minted is recomputed from the pre-settlement deltas. Stated as: the actors'
   balance rise equals the sum of their positive deltas, and the PM rise equals minus the sum of all their deltas.
R2 hook take bound: in groups D (spec 0), F and G, driver delta + hook delta equals the driver delta of the baseline case
   with a zero hook delta and the same actions, per currency, whenever both cases ran every action successfully.
R3 count: a successful unlock ends with count 0, and the count after the last action equals the number of nonzero
   deltas among the three actors.
R4 failed calls: an action that failed leaves the delta count and the pool's slot0 word as they were before it.
R5 solvency: for successful hook-pool cases, the PoolManager holds at least the principal of the position left in range
   (exact fractions, rounded down) in each token currency.
"""
import sys, os, json
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import decode_words, M

def s256(x): return x - (1 << 256) if x >> 255 else x

def sqrt_at_tick(t):
    from decimal import Decimal, getcontext
    getcontext().prec = 80
    return Decimal(1.0001) ** (Decimal(t) / 2) * (Decimal(2) ** 96)

def main():
    cases = json.load(open(sys.argv[1]))['cases']; res = json.load(open(sys.argv[2]))['results']
    viol = []; stats = {'R1': 0, 'R2': 0, 'R3': 0, 'R4': 0, 'R5': 0}
    dec = {}
    for c in cases:
        v = res.get(str(c['id']))
        if not v or not v.get('w'): continue
        d = decode_words([int(x, 16) for x in v['w']], c['nact']); dec[c['id']] = (v['ok'], d)
        deltas = [s256(x) for x in d['deltas']]
        # R3
        nz = sum(1 for x in deltas if x != 0)
        last = d['acts'][-1]['count'] if d['acts'] else 0
        stats['R3'] += 1
        if c['group'] not in ('N7',) and last != nz:
            # deltas of addresses other than the three actors (none expected) would show here
            viol.append({'rule': 'R3', 'case': c['id'], 'tag': c['tag'], 'countAfterActs': last, 'nonzeroActorDeltas': nz})
        if v['ok'] and d['countEnd'] != 0:
            viol.append({'rule': 'R3', 'case': c['id'], 'tag': c['tag'], 'countEnd': d['countEnd']})
        # R4
        pc, ps = 0, 0
        for k, a in enumerate(d['acts']):
            stats['R4'] += 1
            if not a['ok'] and (a['count'] != pc or a['slot0'] != ps):
                viol.append({'rule': 'R4', 'case': c['id'], 'tag': c['tag'], 'act': k, 'before': [pc, hex(ps)], 'after': [a['count'], hex(a['slot0'])]})
            pc, ps = a['count'], a['slot0']
        # R1 (successful unlock only)
        if v['ok']:
            for ci in (0, 1):
                pm_rise = d['bal1'][ci] - d['bal0'][ci]
                act_rise = sum(d['bal1'][2 * j + ci] - d['bal0'][2 * j + ci] for j in (1, 2, 3))
                stats['R1'] += 1
                if c['group'] in ('N', 'N7'):
                    # R1n: native value moves only among the PoolManager, the driver, S and the hook, except a take to an
                    # outside recipient in N7, which must remove exactly the amount when the take succeeded
                    if ci == 0 and c['t0'] == 0:
                        who = (0, 1, 2, 3) if c.get('hooks') else (0, 1, 3)
                        tot = sum(d['bal1'][2 * j] - d['bal0'][2 * j] for j in who)
                        exp = 0
                        r = c.get('recipient')
                        if c['group'] == 'N7' and d['acts'][1]['ok'] and r not in (0x55550000, 0xd0d04000):
                            exp = -c['amount']
                        if c['group'] == 'N7' and r == 0x55550000: exp = 0
                        stats['R1'] += 1
                        if tot != exp:
                            viol.append({'rule': 'R1n', 'case': c['id'], 'tag': c['tag'], 'nativeSum': tot, 'expected': exp})
                    continue
                pos = sum(x for x in deltas[ci::2] if x > 0)
                if act_rise != pos or pm_rise != -sum(deltas[ci::2]):
                    viol.append({'rule': 'R1', 'case': c['id'], 'tag': c['tag'], 'currency': ci, 'pmRise': pm_rise, 'actorsRise': act_rise,
                                 'deltas': deltas[ci::2]})
    # R2 baselines
    base = {}
    for c in cases:
        if c.get('baseline'): base[(c['group'], c.get('zfo'), c.get('amt'), c.get('fn'))] = c['id']
    for c in cases:
        if c['group'] == 'G' and c.get('a0') == 0 and c.get('a1') == 0 and not c.get('bitOff'): base[('G', None, None, c['fn'])] = c['id']
    for c in cases:
        if c['group'] not in ('D', 'F', 'G') or c.get('baseline'): continue
        if c['group'] == 'D' and c.get('spec', 0) != 0: continue
        key = (c['group'], c.get('zfo'), c.get('amt'), c.get('fn')) if c['group'] != 'G' else ('G', None, None, c['fn'])
        b = base.get(key)
        if b is None or c['id'] not in dec or b not in dec: continue
        (_, d), (_, db) = dec[c['id']], dec[b]
        if not all(a['ok'] for a in d['acts']) or not all(a['ok'] for a in db['acts']): continue
        stats['R2'] += 1
        x = [s256(t) for t in d['deltas']]; y = [s256(t) for t in db['deltas']]
        for ci in (0, 1):
            if x[ci] + x[2 + ci] != y[ci] or y[2 + ci] != 0:
                viol.append({'rule': 'R2', 'case': c['id'], 'tag': c['tag'], 'currency': ci, 'driver': x[ci], 'hook': x[2 + ci], 'baselineDriver': y[ci]})
    # R5 solvency of the remaining position (5e17 liquidity on -600..600) for hook groups
    from decimal import Decimal, getcontext
    getcontext().prec = 90
    sa = Fraction(int(sqrt_at_tick(-600))); sb = Fraction(int(sqrt_at_tick(600)))
    for c in cases:
        if c['id'] not in dec or c['group'] not in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'): continue
        ok, d = dec[c['id']]
        if not ok or not all(a['ok'] for a in d['acts'][:4]): continue
        sp = Fraction(d['slot0End'] & ((1 << 160) - 1)); L = Fraction(5 * 10 ** 17)
        if sp <= sa: a0 = L * (sb - sa) * (1 << 96) / (sa * sb); a1 = 0
        elif sp >= sb: a0 = 0; a1 = L * (sb - sa) / (1 << 96)
        else: a0 = L * (sb - sp) * (1 << 96) / (sp * sb); a1 = L * (sp - sa) / (1 << 96)
        stats['R5'] += 1
        # sqrt_at_tick is approximate (Decimal); allow 1e-6 relative slack, which a missing position-size amount exceeds
        for ci, need in ((0, a0), (1, a1)):
            held = d['bal1'][ci] - d['bal0'][ci]
            if held < int(need * Fraction(999999, 1000000)):
                viol.append({'rule': 'R5', 'case': c['id'], 'tag': c['tag'], 'currency': ci, 'held': held, 'principal': int(need)})
    out = {'checked': stats, 'violations': viol}
    json.dump(out, open(sys.argv[3], 'w'), indent=1)
    print(stats, 'violations', len(viol))
    from collections import Counter
    print(Counter(x['rule'] for x in viol))

if __name__ == '__main__':
    main()
