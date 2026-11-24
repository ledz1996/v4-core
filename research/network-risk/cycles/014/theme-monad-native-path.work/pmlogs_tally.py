"""Tally Donate, ERC-6909 Transfer (mint, burn, transfer, transferFrom by spender, burn by spender), Approval and OperatorSet logs of the Monad PoolManager.
src/ERC6909.sol:30,45,53,61,82,88 and src/ERC6909Claims.sol:13-22 fix what each event means. Usage: python3 pmlogs_tally.py <pmlogs.jsonl> <out.json>"""
import sys, json, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
T = {'0x' + keccak(s.encode()).hex(): s.split('(')[0] for s in ['Donate(bytes32,address,uint256,uint256)', 'Transfer(address,address,address,uint256,uint256)', 'Approval(address,address,uint256,uint256)', 'OperatorSet(address,address,bool)']}
c = collections.Counter(); samples = collections.defaultdict(list); lo, hi, win, miss = 1 << 60, 0, 0, 0
def a(t): return '0x' + t[-40:]
for line in open(sys.argv[1]):
    x = json.loads(line); win += 1
    if x['logs'] is None: miss += 1; continue
    lo = min(lo, x['lo']); hi = max(hi, x['hi'])
    for l in x['logs']:
        n = T[l['t'][0]]
        if n == 'Transfer':
            caller = '0x' + l['d'][2 + 24:2 + 64]; frm, to = a(l['t'][1]), a(l['t'][2]); z = '0x' + '0' * 40
            kind = 'mint' if frm == z else ('burn' if to == z else 'transfer')
            if caller != frm and frm != z: kind += 'BySpender'
            n = 'Transfer.' + kind
        c[n] += 1
        if len(samples[n]) < 5: samples[n].append({'tx': l['h'], 'block': l['b']})
json.dump({'windows': win, 'windowsMissing': miss, 'blocks': [lo, hi], 'counts': c, 'samples': samples}, open(sys.argv[2], 'w'), indent=1)
print(win, miss, lo, hi, dict(c))
