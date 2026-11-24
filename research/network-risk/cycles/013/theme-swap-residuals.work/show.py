import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
U = d['unmatched']
def cls(u):
    if u['a0'] == '0' and u['a1'] == '0' and u['pre']['p'] == u['p']: return 'zero'
    return 'other'
print(Counter(cls(u) for u in U))
print('feeMismatch', d['feeCheck']['mismatches'][:5])
for u in [x for x in U if cls(x) == 'other'][:int(sys.argv[2]) if len(sys.argv) > 2 else 4]:
    r = u['result']
    print(u['tx'], u['block'], 'pool', u['pool'][:14], 'key', u['key'] and (u['key']['fee'], u['key']['spacing'], u['key']['hooks']), 'fee', u['fee'])
    print('  pre', u['pre'], ' post p', u['p'], 'tick', u['tick'], 'liq', u['liq'], 'a0', u['a0'], 'a1', u['a1'])
    for t in r.get('tries', [])[:6]: print('   ', t)
    if 'why' in r: print('   why', r['why'])
