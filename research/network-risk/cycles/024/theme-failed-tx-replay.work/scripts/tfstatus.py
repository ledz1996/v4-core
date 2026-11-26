"""Receipts (status, PoolManager log) for trace_filter hits outside the cycle 23 window. usage: tfstatus.py <cid> <url>. Read-only."""
import json, os, sys, time, threading, queue
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS
cid = int(sys.argv[1]); url = sys.argv[2]; PM = NETS[cid]['poolManager'].lower()
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../raw/%d' % cid)
xs = [json.loads(l) for l in open(D + '/find-tf.jsonl')]; xs = [x for x in xs if not x['inWindow']]
v, e = call(url, 'web3_clientVersion', [], 30); open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'tfstatus-start', 'url': url, 'client': v, 't': time.time()}) + '\n')
out = open(D + '/find-zrcpt.jsonl', 'w'); lock = threading.Lock(); q = queue.Queue(); [q.put(x) for x in xs]
def wk():
    while True:
        try: x = q.get_nowait()
        except queue.Empty: return
        for k in range(5):
            r, e = call(url, 'eth_getTransactionReceipt', [x['hash']], 60)
            if r: break
            time.sleep(1 + k)
        if not r: continue
        y = dict(x); y['status'] = r['status']; y['block'] = int(r['blockNumber'], 16); y['index'] = int(r['transactionIndex'], 16)
        y['pmLog'] = any((l.get('address') or '').lower() == PM for l in r['logs'])
        with lock: out.write(json.dumps(y) + '\n')
th = [threading.Thread(target=wk) for _ in range(4)]; [t.start() for t in th]; [t.join() for t in th]; out.close()
v, e = call(url, 'web3_clientVersion', [], 30); open(D + '/brackets.jsonl', 'a').write(json.dumps({'tag': 'tfstatus-end', 'url': url, 'client': v, 't': time.time()}) + '\n')
import collections; print(collections.Counter((y['status'], y['pmLog']) for y in map(json.loads, open(D + '/find-zrcpt.jsonl'))))
