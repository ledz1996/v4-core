import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
from endpoints import *
EXT = '0x1e2eaeaf'  # extsload(bytes32)
def probe(cid):
    out = {'chainId': cid, 'name': NETS[cid]['name']}
    pm = NETS[cid]['poolManager']
    for u in state_urls(cid):
        try:
            head = int(rpc(u, 'eth_blockNumber', [], timeout=20), 16)
            r = {}
            for back in (100, 3000, 100000):
                try:
                    rpc(u, 'eth_call', [{'to': pm, 'data': EXT + '00' * 32}, hex(head - back)], timeout=30); r[back] = 'ok'
                except Exception as e: r[back] = str(e)[:80]
            out[u] = r
        except Exception as e: out[u] = str(e)[:80]
    return out
assert '0x' + keccak(b'extsload(bytes32)')[:4].hex() == EXT
with cf.ThreadPoolExecutor(21) as ex:
    for r in ex.map(probe, sorted(NETS)): print(json.dumps(r))
