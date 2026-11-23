# For owners whose approval is still set: every ERC-6909 Transfer to them (to is topic 2, id is topic 3), then balanceOf(owner, id) at latest.
import sys, json, os, gzip, concurrent.futures as cf
from lib import *
from fetch import getlogs_range
from config import CFG
from state import url, bcall
TR='0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
OVR = {8453: ('https://base.gateway.tenderly.co', 1000), 56: ('https://bsc.api.pocket.network', 5000)}
def run(cid):
    st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid))); lg = json.load(open(os.path.join(HERE, 'raw', 'logs_%d.json' % cid)))
    pm = net(cid)['poolManager']
    owners = sorted({p[0] for p in st['liveOp'] if p[2]} | {p[0] for p in st['liveAl'] if p[3]})
    fn = os.path.join(HERE, 'raw', 'claims_%d.json' % cid)
    if os.path.exists(fn): return cid, 'cached'
    if not owners:
        json.dump(dict(chainId=cid, owners=[], bal=[]), open(fn, 'w')); return cid, 0
    u, chunk = OVR.get(cid) or (CFG[cid]['init'], CFG[cid]['initChunk'])
    ids = {}
    def on(logs):
        for l in logs:
            ids.setdefault('0x' + l['topics'][2][-40:], set()).add(l['topics'][3])
    fails = []
    if cid == 480:
        import requests
        for ow in owners:
            j = requests.get('https://worldchain-mainnet.explorer.alchemy.com/api', params=dict(module='logs', action='getLogs', fromBlock=0, toBlock=lg['toBlock'], address=pm, topic0=TR, topic2=pad_addr(ow), topic0_2_opr='and'), timeout=90, headers={'user-agent': 'curl/8'}).json()
            on([dict(topics=l['topics']) for l in (j.get('result') or [])])
    else:
        for part in [owners[i:i + 200] for i in range(0, len(owners), 200)] * (3 if cid == 56 else 1):  # the BSC source needs three passes, see pocket_bsc.py
            s = getlogs_range(u, {'address': pm, 'topics': [TR, None, [pad_addr(o) for o in part]]}, lg['fromBlock'], lg['toBlock'], chunk, workers=(12 if cid in OVR else 3), on_logs=on, label='claims %d' % cid)
            fails += s['fail']
    pairs = [(o, i) for o, s in ids.items() for i in sorted(s)]
    r = bcall(url(cid), [('eth_call', [{'to': pm, 'data': '0x00fdd58e' + adr(o) + i[2:]}, 'latest']) for o, i in pairs])
    bal = [[o, i, (int(v, 16) if isinstance(v, str) and len(v) > 2 else None)] for (o, i), v in zip(pairs, r)]
    json.dump(dict(chainId=cid, owners=owners, fails=fails, bal=bal), open(fn, 'w'))
    return cid, 'owners', len(owners), 'with transfers', len(ids), 'pairs', len(pairs), 'nonzero', sum(1 for b in bal if b[2]), 'fails', len(fails)
if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]]
    with cf.ThreadPoolExecutor(len(ids)) as ex:
        for r in ex.map(run, ids): print(r, flush=True)
