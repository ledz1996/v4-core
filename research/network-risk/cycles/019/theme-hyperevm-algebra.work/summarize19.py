"""Sum the per-swap and per-group lines of v3strict19.py and alg19.py. Usage: summarize19.py strict|alg <out.json> <prefix>..."""
import sys, json, collections, glob
kind, outp, prefixes = sys.argv[1], sys.argv[2], sys.argv[3:]
C = collections.Counter(); G = collections.Counter(); other = collections.Counter(); mis = []; seen = set(); errs = []
for pre in prefixes:
    for f in sorted(glob.glob(pre + '*.groups.jsonl')):
        for l in open(f):
            x = json.loads(l); g = tuple(x['g'])
            if g in seen: C['duplicateGroupLines'] += 1; continue
            seen.add(g)
            if 'error' in x: errs.append(x); continue
            G['groups'] += 1
            for k, v in x['counts'].items(): G[k] += v
            for k, v in x.get('other', {}).items(): other[k] += v
            if kind == 'strict' and x.get('feeSeq'): G['groupsWithFeeAdjustment'] += 1
            if kind == 'alg' and x.get('unknown'): G['groupsWithUnknownTopic'] += 1
    for f in sorted(glob.glob(pre + '*.swaps.jsonl')):
        for l in open(f):
            x = json.loads(l)
            if kind == 'strict':
                if x.get('kind') == 'zero': continue
                L, S = x['lenient'], x['strict']
                c18 = bool(L and L['m512'])
                C['swaps'] += 1
                if c18: C['c18_m512'] += 1
                if not S.get('fail'):
                    C['strictOk'] += 1; C['strictMode:' + S['mode']] += 1
                    C['strictMultiStep' if S['steps'] > 1 else 'strictOneStep'] += 1
                    if S['m512']: C['strictM512'] += 1; C['strictM512calls'] += S['m512']
                    if x.get('needBranch'): C['needBranch'] += 1
                    if c18:
                        C['c18_m512_strictOk'] += 1
                        if S['m512']: C['c18_m512_strictM512'] += 1
                        if x.get('needBranch'): C['c18_m512_needBranch'] += 1
                        if L['mode'] == 'feeSearch' or L.get('limitAtLogged') is not None: C['c18_m512_lenientFeeSearch'] += 1
                else:
                    C['strictFail'] += 1; mis.append(x)
                    if c18: C['c18_m512_strictFail'] += 1
            else:
                r = x['res']; C['swaps'] += 1
                if r.get('fail'): C['mismatch'] += 1; mis.append(x)
                else:
                    C['ok'] += 1; C['mode:' + r['mode']] += 1; C['multiStep' if r['steps'] > 1 else 'oneStep'] += 1
                    if r['crossed']: C['crossedTick'] += 1
                    if r['m512']: C['m512'] += 1; C['m512calls'] += r['m512']
                    if r['fallback']: C['fallback'] += 1
                    if x.get('needBranch'): C['needBranch'] += 1
                    fs = x['feeSource']
                    if fs.get('swapFeeLog'): C['feeFromSwapFeeLog'] += 1
                    if fs.get('overrideFee'): C['overrideFeeNonzero'] += 1
                    if fs.get('pluginFee'): C['pluginFeeNonzero'] += 1
json.dump({'swapCounts': C, 'groupCounts': G, 'otherTopics': other, 'groupErrors': errs, 'mismatches': mis}, open(outp, 'w'), indent=1)
print(json.dumps({'swapCounts': C, 'groupCounts': G, 'otherTopics': other, 'groupErrors': len(errs), 'mismatches': len(mis)})[:4000])
