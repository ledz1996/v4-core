# X Layer Initialize history through xlayer-mainnet.rpc.sentio.xyz, which serves eth_getLogs in windows of 1,000 blocks back to the
# deployment block 46,106,392 (rpc.xlayer.tech serves 100 blocks; rpc.nodeflare.app serves 100,000 blocks for 17 calls a day).
# Resumable through raw/init_196.jsonl. Writes raw/init_196.json.gz and raw/currencies_196.json.gz at the end. Read-only: eth_getLogs.
import sys, json, gzip, time, os, threading
from concurrent.futures import ThreadPoolExecutor
from lib import *
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
U = 'https://xlayer-mainnet.rpc.sentio.xyz'; pm = net(196)['poolManager']; LO = 46106000
head = int(rpc('https://rpc.xlayer.tech', 'eth_blockNumber', []), 16) - 50
FN = 'raw/init_196.jsonl'; done = set(); rows = []
if os.path.exists(FN):
    for l in open(FN):
        x = json.loads(l)
        if x[0] == 'w': done.add(x[1])
        else: rows.append(x[1])
out = open(FN, 'a'); lock = threading.Lock(); st = {'n': 0, 'fail': []}
wins = [a for a in range(LO, head + 1, 1000) if a not in done]
print('todo', len(wins), 'done', len(done), flush=True)
def one(a):
    b = min(a + 999, head)
    for k in range(10):
        try:
            j = post(U, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [INIT], 'fromBlock': hex(a), 'toBlock': hex(b)}]}, timeout=40, tries=2)
        except Exception as e:
            time.sleep(2 + 2 * k); continue
        if 'error' in j or 'result' not in j: time.sleep(2 + 2 * k); continue
        with lock:
            for l in j['result']:
                d = l['data'][2:]; t = l['topics']
                r = [int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), '0x' + d[128:192][-40:], l['transactionHash']]
                rows.append(r); out.write(json.dumps(['r', r]) + '\n')
            out.write(json.dumps(['w', a]) + '\n'); st['n'] += 1
            if st['n'] % 1000 == 0: out.flush(); print('windows', st['n'], len(wins), 'rows', len(rows), time.strftime('%H:%M:%S'), flush=True)
        return
    with lock: st['fail'].append(a)
with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as ex: list(ex.map(one, wins))
out.close(); rows.sort(); cur = {}
for r in rows:
    for c in (r[2], r[3]):
        e = cur.setdefault(c, [0, r[0]]); e[0] += 1
json.dump(dict(chainId=196, url=U, lo=46106392, hi=head, nFail=len(st['fail']), fail=st['fail'], rows=rows), gzip.open('raw/init_196.json.gz', 'wt'))
json.dump(dict(chainId=196, lo=46106392, hi=head, pools=len(rows), currencies=cur), gzip.open('raw/currencies_196.json.gz', 'wt'))
print(196, 'pools', len(rows), 'currencies', len(cur), 'fail', len(st['fail']), flush=True)
