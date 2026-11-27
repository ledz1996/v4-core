"""Copied in cycle 33 from cycles/031/ethereum-reference.work/scripts. Cycle 29 ethereum-reference, leads L-1149 and L-1136. Runs the battery, the targeted set and the 14,598 cycle 27
edge vectors on one endpoint, sending every batch R times. Each send is one JSON-RPC batch
[web3_clientVersion, eth_call, web3_clientVersion]; the two version strings are recorded, but on a gateway that routes
every element on its own they do not prove which backend ran the call. With R sends per batch, a backend that serves a
share p of requests runs each batch at least once with probability 1 - (1 - p)^R. Read-only (eth_call with a state
override). Usage: python3 repeatrun.py <out.json> <url> <R> [batch size]"""
import sys, json, threading, time, collections, urllib.request, ssl, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/027/ethereum-reference.work')
import evm, battery, targeted, pinrun
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def post(url, body, timeout=120):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r: return json.loads(r.read())
def main():
    out, url, R = sys.argv[1], sys.argv[2], int(sys.argv[3]); size = int(sys.argv[4]) if len(sys.argv) > 4 else 600
    code = battery.dispatcher(); V = battery.vectors() + targeted.vectors() + pinrun.extra()
    batches = [V[i:i + size] for i in range(0, len(V), size)]
    lock = threading.Lock(); bad = []; st = collections.Counter(); seen = collections.Counter(); perBatch = {}
    def one(bi):
        batch = batches[bi]; data = battery.encode(batch); exp = battery.expected(batch, data); got = 0
        for r in range(R):
            for t in range(6):
                try:
                    res = post(url, [{'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []},
                                     {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': evm.STUB, 'data': '0x' + data.hex()}, 'latest', {evm.STUB: {'code': '0x' + code.hex()}}]},
                                     {'jsonrpc': '2.0', 'id': 2, 'method': 'web3_clientVersion', 'params': []}])
                    m = {x['id']: x for x in res}
                    if 'result' not in m[1]: raise Exception(str(m[1].get('error'))[:100])
                    w = bytes.fromhex(m[1]['result'][2:])
                    if len(w) != 32 * len(batch): raise Exception('len')
                    b, a = m[0].get('result'), m[2].get('result')
                    mm = [{'op': tup[0], 'a': hex(tup[1]), 'b': hex(tup[2]), 'c': hex(tup[3]), 'got': hex(int.from_bytes(w[32 * k:32 * k + 32], 'big')), 'want': hex(e), 'before': b, 'after': a}
                          for k, (tup, e) in enumerate(zip(batch, exp)) if int.from_bytes(w[32 * k:32 * k + 32], 'big') != e]
                    with lock:
                        st['sends'] += 1; seen[b] += 1; seen[a] += 1; bad.extend(mm)
                        if a == b: st['bracketEqual'] += 1
                    got += 1; break
                except Exception as e:
                    with lock: st['errors'] += 1
                    time.sleep(2 + t)
        with lock: perBatch[bi] = got
    with cf.ThreadPoolExecutor(4) as ex: list(ex.map(one, range(len(batches))))
    r = {'url': url, 'R': R, 'vectors': len(V), 'batches': len(batches), 'batchesRunAtLeastOnce': sum(1 for v in perBatch.values() if v),
         'batchesRunRTimes': sum(1 for v in perBatch.values() if v == R), 'mismatchCount': len(bad), 'mismatches': bad[:200],
         'stats': dict(st), 'versionsSeenInBrackets': dict(seen)}
    json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'}, indent=1))
if __name__ == '__main__': main()
