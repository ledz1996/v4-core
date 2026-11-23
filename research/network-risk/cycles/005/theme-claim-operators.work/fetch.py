# Adaptive eth_getLogs over a block range: split a chunk in two when the endpoint refuses it.
import time, threading, concurrent.futures as cf
from lib import *
def getlogs_range(url, flt, lo, hi, chunk, workers=4, on_logs=None, label=''):
    """Fetch logs for blocks lo..hi inclusive. on_logs(list) is called per chunk (thread safe caller)."""
    lock = threading.Lock(); stats = {'req': 0, 'logs': 0, 'fail': []}
    def one(a, b, depth=0):
        f = dict(flt); f['fromBlock'] = hex(a); f['toBlock'] = hex(b)
        for attempt in range(6):
            try:
                with lock: stats['req'] += 1
                j = post(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [f]}, timeout=60, tries=5)
            except Exception as e:
                time.sleep(2 + attempt * 2); continue
            if 'error' in j:
                msg = json.dumps(j['error']).lower()
                if any(k in msg for k in ('rate', 'too many requests', 'capacity', 'timeout', 'timed out', 'busy', 'try again')) and 'range' not in msg and 'limit exceeded' not in msg:
                    time.sleep(2 + attempt * 2); continue
                if b > a:
                    m = (a + b) // 2; one(a, m, depth + 1); one(m + 1, b, depth + 1); return
                with lock: stats['fail'].append((a, b, msg[:120]))
                return
            r = j['result']
            with lock:
                stats['logs'] += len(r)
                if on_logs: on_logs(r)
            return
        if b > a:
            m = (a + b) // 2; one(a, m, depth + 1); one(m + 1, b, depth + 1); return
        with lock: stats['fail'].append((a, b, 'gave up'))
    chunks = [(a, min(a + chunk - 1, hi)) for a in range(lo, hi + 1, chunk)]
    done = 0
    with cf.ThreadPoolExecutor(workers) as ex:
        for _ in ex.map(lambda c: one(*c), chunks):
            done += 1
            if done % 200 == 0: print(label, 'chunks', done, '/', len(chunks), 'logs', stats['logs'], flush=True)
    return stats
