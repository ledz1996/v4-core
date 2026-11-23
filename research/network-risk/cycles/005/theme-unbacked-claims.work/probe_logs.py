# Probe: how wide a block range each log endpoint serves for the ERC-6909 mint filter, and how many mints the last span holds.
import sys, json, concurrent.futures as cf
from lib import *
from config import CFG
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
Z = '0x' + '0' * 64
def probe(cid):
    n = net(cid); pm = n['poolManager']; out = {'chainId': cid, 'name': n['name']}
    urls = []
    for u in [CFG[cid]['logs'], CFG[cid].get('init'), n['rpc']] + CFG[cid]['state']:
        if u and u not in urls: urls.append(u)
    out['urls'] = {}
    for u in urls:
        o = {}
        try:
            head = int(rpc(u, 'eth_blockNumber', []), 16); o['head'] = head
            for span in (2000000, 500000, 100000, 10000, 2000, 500, 100):
                try:
                    r = rpc(u, 'eth_getLogs', [{'address': pm, 'topics': [T6909, Z], 'fromBlock': hex(max(0, head - span)), 'toBlock': hex(head)}], timeout=60, tries=2)
                    o['span'] = span; o['mints'] = len(r); break
                except Exception as e:
                    o['err%d' % span] = str(e)[:140]
        except Exception as e:
            o['err'] = str(e)[:140]
        out['urls'][u] = o
    return out
if __name__ == '__main__':
    with cf.ThreadPoolExecutor(21) as ex:
        res = list(ex.map(probe, list(CFG)))
    json.dump(res, open('raw/probe_logs.json', 'w'), indent=1)
    for r in res:
        print(r['chainId'], r['name'])
        for u, o in r['urls'].items(): print('   ', u, o.get('head'), 'span', o.get('span'), 'mints', o.get('mints'), [v for k, v in o.items() if k.startswith('err')][:1])
