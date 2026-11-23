# X Layer: public endpoints cap eth_getLogs at 100 blocks, so the history is read in 100 block windows,
# newest first, over three endpoints. Progress is checkpointed so the covered range is known exactly.
import sys, json, os, time, threading, queue, requests
from lib import *
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
CID = 196; pm = net(CID)['poolManager']; DEP = 46106392
EPS = [('https://rpc.xlayer.tech', 10), ('https://xlayerrpc.okx.com', 10), ('https://xlayer.drpc.org', 12)]
FN = os.path.join(HERE, 'raw', 'logs_196.json')
st = json.load(open(FN)) if os.path.exists(FN) else None
if not st:
    head = int(rpc(EPS[0][0], 'eth_blockNumber', []), 16)
    st = dict(chainId=CID, poolManager=pm, fromBlock=DEP, toBlock=head, chunk=100, done=[], logs=[], urls=[e[0] for e in EPS])
head = st['toBlock']; done = set(st['done']); logs = st['logs']
q = queue.Queue()
for a in range(head - (head - DEP) % 100, DEP - 100, -100):
    if a not in done: q.put(a)
lock = threading.Lock(); cnt = [0]; stop = time.time() + float(sys.argv[1]) if len(sys.argv) > 1 else 1e18
def save():
    json.dump(dict(st, done=sorted(done), logs=logs), open(FN + '.tmp', 'w')); os.replace(FN + '.tmp', FN)
def work(u):
    s = requests.Session(); s.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'}); back = 0.2
    while time.time() < stop:
        try: a = q.get_nowait()
        except queue.Empty: return
        b = min(a + 99, head)
        try:
            j = s.post(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [[OP, AP]], 'fromBlock': hex(max(a, DEP)), 'toBlock': hex(b)}]}), timeout=30).json()
            r = j['result']
        except Exception:
            q.put(a); time.sleep(back); back = min(back * 1.5, 5); continue
        back = 0.2
        with lock:
            done.add(a); cnt[0] += 1
            logs.extend(dict(b=int(l['blockNumber'], 16), tx=l['transactionHash'], t=l['topics'], d=l['data']) for l in r)
            if cnt[0] % 5000 == 0:
                save(); print(time.strftime('%H:%M:%S'), 'done', len(done), 'left', q.qsize(), 'logs', len(logs), flush=True)
ths = [threading.Thread(target=work, args=(u,)) for u, n in EPS for _ in range(n)]
for t in ths: t.start()
for t in ths: t.join()
with lock: save()
print('exit done', len(done), 'left', q.qsize(), 'logs', len(logs))
