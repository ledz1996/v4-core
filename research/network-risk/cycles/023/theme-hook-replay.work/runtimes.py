"""Fetch runtime code of each replay candidate hook on each network where it has code, and list opcodes and PUSH20 constants of interest. Read only."""
import sys, json, hashlib
sys.path.insert(0, '.')
from rpcu import rpc
from evmdis import dis
X = json.load(open('/home/user/v4-core/research/network-risk/cycles/022/theme-empty-hook-pools.work/raw/xchain.json'))
URL = {c: r['url'] for c, r in X['chains'].items()}
NETS = {str(n['chainId']): n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
PMS = {n['poolManager'].lower(): c for c, n in NETS.items()}
out = {'client': {}, 'hooks': {}}
for h in X['hooks']:
    s = {c: X['chains'][c]['size'].get(h) for c in X['chains'] if 'size' in X['chains'][c]}
    w = [c for c, v in s.items() if v and v != 23]
    if not w: continue
    out['hooks'][h] = {}
    for c in w:
        u = URL[c]
        if c not in out['client']: out['client'][c] = rpc(u, 'web3_clientVersion', [])
        code = rpc(u, 'eth_getCode', [h, 'latest'])
        b = bytes.fromhex(code[2:]); d = dis(b)
        ops = {}
        for pc, n, a in d:
            if n in ('ORIGIN', 'SSTORE', 'CHAINID', 'DELEGATECALL', 'SELFDESTRUCT', 'CREATE', 'CREATE2', 'CALLCODE'): ops[n] = ops.get(n, 0) + 1
        p20 = sorted({a for pc, n, a in d if n == 'PUSH20'})
        out['hooks'][h][c] = {'len': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'ops': ops,
                              'push20': [(a, PMS.get('0x' + a, '')) for a in p20], 'eip1167': code[:22] == '0x363d3d373d3d3d363d73'}
        print(h, c, out['hooks'][h][c], flush=True)
for c in out['client']: out['client'][c] = [out['client'][c], rpc(URL[c], 'web3_clientVersion', [])]
json.dump(out, open('raw/runtimes.json', 'w'), indent=1)
