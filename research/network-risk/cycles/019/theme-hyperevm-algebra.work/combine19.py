"""Final Task 1 counts: pass 1 (out/strict-*) with the groups of pass 2 (out/strict2, --trace-args) replaced."""
import json, collections, glob
p2 = set(tuple(x) for x in json.load(open('out/strict-pass2-groups.json')))
C = collections.Counter(); fac = collections.Counter(); facNeed = collections.Counter()
pools = json.load(open('/home/user/v4-core/research/network-risk/cycles/015/theme-closed-producers-2.work/raw/pools999.json'))['pools']
def take(x):
    if x.get('kind') == 'zero': C['zeroSwaps'] += 1; return
    L, S = x['lenient'], x['strict']; c18 = bool(L and L['m512'])
    C['swaps'] += 1
    if not c18: return
    C['c18_m512'] += 1
    lenient_lax = L['mode'] == 'feeSearch' or L['mode'].startswith('toLimit') or L.get('limitAtLogged')
    if S.get('fail'): C['c18_m512_strictFail'] += 1; return
    C['c18_m512_strictOk'] += 1; C['strictMode:' + S['mode']] += 1
    C['strictMultiStep' if S['steps'] > 1 else 'strictOneStep'] += 1
    if S['m512']: C['c18_m512_strictM512'] += 1; C['m512calls'] += S['m512']
    f = pools[x['pool']]['factory']; fac[f] += 1
    if x.get('needBranch'): C['c18_m512_needBranch'] += 1; facNeed[f] += 1
    if lenient_lax: C['c18_m512_lenientWasFeeSearch'] += 1
for f in sorted(glob.glob('out/strict-[0-3].swaps.jsonl')):
    for l in open(f):
        x = json.loads(l)
        if (x['pool'], x['block']) not in p2: take(x)
for l in open('out/strict2.swaps.jsonl'): take(json.loads(l))
out = {'counts': C, 'byFactory': fac, 'needBranchByFactory': facNeed}
json.dump(out, open('out/strict-final-summary.json', 'w'), indent=1); print(json.dumps(out))
