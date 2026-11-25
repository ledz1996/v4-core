"""Read-only eth_call: TokenRollbackProbe placed by state override at the PoolManager address of a network (so that
it holds what the PoolManager holds), transferring 1 unit of a node-implemented token inside frames that revert
or halt. Usage: python3 rb.py <out.json>"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
B = json.load(open('/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/build/TokenRollbackProbe.json'))
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
TO = '0x000000000000000000000000000000000dead016'
CASES = [  # chain, url, token, mode, balance override (native wei) or None, label
    (1, None, '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 0, None, 'Ethereum USDC (bytecode token, control)'),
    (8453, 'https://base-rpc.publicnode.com', '0xB2000000000000000000002fEb517dFeC7415344', 0, None, 'Base B20 OUSD'),
    (8453, 'https://base-rpc.publicnode.com', '0xb2000000000000000000000d8ce462e99ee7a47b', 0, None, 'Base B20 AMDc'),
    (4217, None, '0x20c0000000000000000000000000000000000000', 0, None, 'Tempo TIP-20 pathUSD'),
    (42220, 'https://forno.celo.org', '0x471EcE3750Da237f93B8E339c536989b8978a438', 0, 10**18, 'Celo CELO ERC-20 face'),
    (42220, 'https://forno.celo.org', '0x471EcE3750Da237f93B8E339c536989b8978a438', 1, 10**18, 'Celo native value, face read'),
    (5042, None, '0x3600000000000000000000000000000000000000', 0, 10**18, 'Arc USDC ERC-20 face'),
    (5042, None, '0x3600000000000000000000000000000000000000', 1, 10**18, 'Arc native value, face read'),
]
def sel(s): return keccak(s.encode())[:4].hex()
def w(x): return x.to_bytes(32, 'big').hex()
out = []
for cid, url, tok, mode, bal, label in CASES:
    url = url or nets[cid]['rpc']; pm = nets[cid]['poolManager']
    ov = {pm: {'code': '0x' + B['runtime']}}
    if bal is not None: ov[pm]['balance'] = hex(bal)
    data = '0x' + sel('run(address,address,uint256,uint256)') + w(int(tok, 16)) + w(int(TO, 16)) + w(1) + w(mode)
    rec = {'chain': cid, 'label': label, 'token': tok, 'holder': pm, 'mode': mode}
    for k in range(4):
        try:
            r = rpc(url, 'eth_call', [{'from': '0x00000000000000000000000000000000000a11ce', 'to': pm, 'data': data, 'gas': hex(20_000_000)}, 'latest', ov], timeout=90)
            b = bytes.fromhex(r[2:]); ws = [int.from_bytes(b[i:i + 32], 'big') for i in range(64, len(b), 32)]
            rows = [ws[i:i + 10] for i in range(0, len(ws), 10)]
            rec['rows'] = rows
            # a halted or static frame must leave all four balances as they were; the control (kind 0) must move one unit
            rec['leaks'] = [x[0] for x in rows if x[0] != 0 and x[2:6] != x[6:10]]
            c = [x for x in rows if x[0] == 0][0]
            rec['controlMoved'] = c[1] == 1 and c[2:6] != c[6:10]
            rec['staticRefused'] = [x for x in rows if x[0] == 9][0][1] == 0
            break
        except Exception as e:
            rec['err'] = str(e)[:200]; time.sleep(3)
    out.append(rec); print(cid, label, rec.get('leaks'), 'control', rec.get('controlMoved'), 'staticRefused', rec.get('staticRefused'), rec.get('err', '') if 'rows' not in rec else '')
json.dump(out, open(sys.argv[1], 'w'), indent=1)
