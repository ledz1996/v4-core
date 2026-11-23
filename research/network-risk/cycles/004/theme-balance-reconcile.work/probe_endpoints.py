# Probe each endpoint: head, multicall3 code, old state depth, getLogs range for Initialize.
import json, sys, concurrent.futures as cf
from lib import *
from keccak import keccak256
INIT = '0x' + keccak256(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
print('Initialize topic0', INIT)
def probe(n):
    u = n['rpc']; pm = n['poolManager']; o = {'chainId': n['chainId'], 'name': n['name']}
    try:
        head = int(rpc(u, 'eth_blockNumber', []), 16); o['head'] = head
        b = rpc(u, 'eth_getBlockByNumber', [hex(head), False]); t1 = int(b['timestamp'], 16)
        b0 = rpc(u, 'eth_getBlockByNumber', [hex(head - 10000), False]); t0 = int(b0['timestamp'], 16)
        o['blockTime'] = round((t1 - t0) / 10000, 3)
        o['mc3'] = (len(rpc(u, 'eth_getCode', [MC3, 'latest'])) - 2) // 2
        day = int(86400 / max(o['blockTime'], 0.01))
        o['dayBlocks'] = day
        for back in (day * 30, day * 7, day, day // 4, 10000, 1000, 100):
            try:
                rpc(u, 'eth_call', [{'to': pm, 'data': '0x8da5cb5b'}, hex(head - back)]); o['stateBack'] = back; break
            except Exception as e:
                o['stateErr'] = str(e)[:100]
        for span in (5000000, 1000000, 100000, 50000, 10000, 5000, 2000, 1000, 500, 100):
            try:
                r = rpc(u, 'eth_getLogs', [{'address': pm, 'topics': [INIT], 'fromBlock': hex(head - span), 'toBlock': hex(head)}])
                o['logSpan'] = span; o['initLogsInSpan'] = len(r); break
            except Exception as e:
                o['logErr'] = str(e)[:140]
        try:
            r = batch(u, [('eth_blockNumber', [])] * 50); o['batch50'] = sum(1 for x in r if isinstance(x, str))
        except Exception as e:
            o['batchErr'] = str(e)[:100]
    except Exception as e:
        o['err'] = str(e)[:200]
    return o
with cf.ThreadPoolExecutor(21) as ex: res = list(ex.map(probe, NETS))
json.dump({'initTopic': INIT, 'probe': res}, open('raw/endpoints.json', 'w'), indent=1)
for r in res: print(json.dumps(r))
