"""Binary search of the first block at which each replay candidate hook has code, on each network where it has code. Read only (eth_getCode, eth_getTransactionCount)."""
import sys, json, time
sys.path.insert(0, '.')
from rpcu import rpc
X = json.load(open('/home/user/v4-core/research/network-risk/cycles/022/theme-empty-hook-pools.work/raw/xchain.json'))
URL = {c: r['url'] for c, r in X['chains'].items()}
URL['56'] = 'https://bsc.gateway.tenderly.co'
cand = {}
for h in X['hooks']:
    s = {c: X['chains'][c]['size'].get(h) for c in X['chains'] if 'size' in X['chains'][c]}
    w = [c for c, v in s.items() if v and v != 23]
    if w: cand[h] = w
out = {'urls': URL, 'client': {}, 'hooks': {}}
for h, cs in cand.items():
    out['hooks'][h] = {}
    for c in cs:
        u = URL[c]
        try:
            if c not in out['client']: out['client'][c] = rpc(u, 'web3_clientVersion', [])
            hi = int(rpc(u, 'eth_blockNumber', []), 16); lo = 0
            if len(rpc(u, 'eth_getCode', [h, hex(hi)])) <= 2: out['hooks'][h][c] = {'error': 'no code at head'}; continue
            while hi - lo > 1:
                m = (lo + hi) // 2
                if len(rpc(u, 'eth_getCode', [h, hex(m)])) > 2: hi = m
                else: lo = m
            code = rpc(u, 'eth_getCode', [h, hex(hi)])
            out['hooks'][h][c] = {'createdAtBlock': hi, 'codeLen': (len(code) - 2) // 2, 'nonceAtHead': int(rpc(u, 'eth_getTransactionCount', [h, 'latest']), 16)}
        except Exception as e: out['hooks'][h][c] = {'error': str(e)[:300]}
        print(h, c, out['hooks'][h][c], flush=True)
for c in out['client']: out['client'][c] = [out['client'][c], rpc(URL[c], 'web3_clientVersion', [])]
json.dump(out, open('raw/createblock.json', 'w'), indent=1)
