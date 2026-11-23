# X Layer endpoints cap eth_getLogs at 100 blocks. Walk backward from the head in 100 block steps, rate limited,
# and append Initialize logs to raw/init_196_back.jsonl. Read-only.
import sys, json, time, threading
from lib import *
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
pm = net(196)['poolManager']; URLS = ['https://rpc.xlayer.tech', 'https://xlayerrpc.okx.com', 'https://xlayer.drpc.org']
head = int(rpc(URLS[0], 'eth_blockNumber', []), 16) - 5
stop = int(sys.argv[1]); delay = float(sys.argv[2])
lock = threading.Lock(); state = {'next': head, 'done': 0, 'logs': 0, 'low': head}
out = open('raw/init_196_back.jsonl', 'a')
def worker(u):
    while True:
        with lock:
            b = state['next']
            if b <= stop: return
            a = max(stop, b - 99); state['next'] = a - 1
        for attempt in range(30):
            try:
                j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [INIT], 'fromBlock': hex(a), 'toBlock': hex(b)}]}, tries=2)
                if 'error' in j: time.sleep(1 + attempt); continue
                with lock:
                    for l in j['result']:
                        d = l['data'][2:]; t = l['topics']
                        out.write(json.dumps([int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), '0x' + d[128:192][-40:], l['transactionHash']]) + '\n')
                    out.flush(); state['done'] += 1; state['logs'] += len(j['result']); state['low'] = min(state['low'], a)
                    if state['done'] % 500 == 0: print('done', state['done'], 'logs', state['logs'], 'low', state['low'], 'head', head, flush=True)
                break
            except Exception as e:
                time.sleep(2 + attempt)
        else:
            print('gave up', a, b, flush=True)
        time.sleep(delay)
ts = [threading.Thread(target=worker, args=(u,)) for u in URLS for _ in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
print('finished', state, flush=True)
