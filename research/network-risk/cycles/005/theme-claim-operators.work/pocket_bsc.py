# BNB Smart Chain, second source. The Pocket gateway serves 5000 block windows but some of its backends answer an old window with an empty list,
# so every window is asked until three answers arrive and the union is kept. Oldest first; the Tenderly scan runs newest first.
import sys, json, os, time, threading, queue, requests
from lib import *
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
CID = 56; pm = net(CID)['poolManager']; DEP = 45900000; CH = 5000; U = 'https://bsc.api.pocket.network'; K = 3
FN = os.path.join(HERE, 'raw', 'logs_56_pocket.json')
st = json.load(open(FN)) if os.path.exists(FN) else None
if not st:
    head = int(rpc('https://bnb.gateway.tenderly.co', 'eth_blockNumber', []), 16)
    st = dict(chainId=CID, poolManager=pm, fromBlock=DEP, toBlock=head, chunk=CH, answersPerWindow=K, done=[], logs={}, disagree=0, urls=[U])
head = st['toBlock']; done = set(st['done']); logs = st['logs']
q = queue.Queue()
for a in range(DEP, head + 1, CH):
    if a not in done: q.put(a)
lock = threading.Lock(); cnt = [0]
def save():
    json.dump(dict(st, done=sorted(done), logs=logs), open(FN + '.tmp', 'w')); os.replace(FN + '.tmp', FN)
def work():
    s = requests.Session(); s.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
    while True:
        try: a = q.get_nowait()
        except queue.Empty: return
        b = min(a + CH - 1, head); got = []; tries = 0
        while len(got) < K and tries < 40:
            tries += 1
            try:
                j = s.post(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [[OP, AP]], 'fromBlock': hex(a), 'toBlock': hex(b)}]}), timeout=40).json()
                got.append(j['result'])
            except Exception:
                time.sleep(0.3)
        if len(got) < K: q.put(a); continue
        with lock:
            if len({len(g) for g in got}) > 1: st['disagree'] += 1
            for g in got:
                for l in g: logs[l['transactionHash'] + ':' + l['logIndex']] = dict(b=int(l['blockNumber'], 16), tx=l['transactionHash'], t=l['topics'], d=l['data'])
            done.add(a); cnt[0] += 1
            if cnt[0] % 500 == 0:
                save(); print(time.strftime('%H:%M:%S'), 'done', len(done), 'left', q.qsize(), 'logs', len(logs), 'disagree', st['disagree'], flush=True)
ths = [threading.Thread(target=work) for _ in range(16)]
for t in ths: t.start()
for t in ths: t.join()
save(); print('exit done', len(done), 'left', q.qsize(), 'logs', len(logs), 'disagree', st['disagree'])
