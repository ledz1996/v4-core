# BNB Smart Chain: ERC-6909 Transfer logs to owners with a live approval, 5000 block windows from the Pocket gateway.
# Each window is asked until K answers arrive and the union is kept (some backends answer old windows with an empty list). Checkpointed.
import sys, json, os, time, threading, queue, requests
from lib import *
TR='0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
CID = 56; pm = net(CID)['poolManager']; CH = 5000; U = 'https://bsc.api.pocket.network'; K = 2
lg = json.load(open(os.path.join(HERE, 'raw', 'logs_56.json'))); st0 = json.load(open(os.path.join(HERE, 'raw', 'state_56.json')))
owners = sorted({p[0] for p in st0['liveOp'] if p[2]} | {p[0] for p in st0['liveAl'] if p[3]})
FN = os.path.join(HERE, 'raw', 'claimlogs_56.json')
st = json.load(open(FN)) if os.path.exists(FN) else dict(chainId=CID, fromBlock=lg['fromBlock'], toBlock=lg['toBlock'], chunk=CH, answersPerWindow=K, owners=owners, done=[], ids={}, disagree=0, nlogs=0)
DEP = st['fromBlock']; head = st['toBlock']; done = set(st['done']); ids = {o: set(v) for o, v in st['ids'].items()}
q = queue.Queue()
for a in range(DEP, head + 1, CH):
    if a not in done: q.put(a)
lock = threading.Lock(); cnt = [0]
def save():
    json.dump(dict(st, done=sorted(done), ids={o: sorted(v) for o, v in ids.items()}), open(FN + '.tmp', 'w')); os.replace(FN + '.tmp', FN)
def work():
    s = requests.Session(); s.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
    while True:
        try: a = q.get_nowait()
        except queue.Empty: return
        b = min(a + CH - 1, head); got = []; tries = 0
        while len(got) < K and tries < 40:
            tries += 1
            try:
                j = s.post(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [TR, None, [pad_addr(o) for o in owners]], 'fromBlock': hex(a), 'toBlock': hex(b)}]}), timeout=40).json()
                got.append(j['result'])
            except Exception:
                time.sleep(0.3)
        if len(got) < K: q.put(a); continue
        with lock:
            if len({len(g) for g in got}) > 1: st['disagree'] += 1
            for g in got:
                for l in g: ids.setdefault('0x' + l['topics'][2][-40:], set()).add(l['topics'][3])
            st['nlogs'] += max(len(g) for g in got)
            done.add(a); cnt[0] += 1
            if cnt[0] % 500 == 0:
                save(); print(time.strftime('%H:%M:%S'), 'done', len(done), 'left', q.qsize(), 'logs', st['nlogs'], 'disagree', st['disagree'], flush=True)
ths = [threading.Thread(target=work) for _ in range(24)]
for t in ths: t.start()
for t in ths: t.join()
with lock: save()
print('exit done', len(done), 'left', q.qsize(), 'logs', st['nlogs'], 'disagree', st['disagree'])
