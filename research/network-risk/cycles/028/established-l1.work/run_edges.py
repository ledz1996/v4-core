"""Cycle 28 established-l1: send the cycle 27 vectors (15,510 large-index vectors of
cycles/027/op-stack-eth.work/scripts/hiword.py and 14,598 edge vectors of
cycles/027/ethereum-reference.work/pinrun.py extra()) to one endpoint. Each batch goes in one
HTTP request as [web3_clientVersion, eth_call, web3_clientVersion]; the batch is credited to a
build only when both version strings agree. Read-only: eth_call with a state override.
Usage: python3 run_edges.py <out.json> <url> [batch] [threads]"""
import sys, json, time, threading, urllib.request, concurrent.futures as cf
R = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, R + '/tools/opdiff')
sys.path.insert(0, R + '/cycles/027/op-stack-eth.work/scripts')
sys.path.insert(0, R + '/cycles/027/ethereum-reference.work')
import evm, battery, hiword, pinrun

def post(url, body, timeout=90):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def main():
    out, url = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    threads = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    code = battery.dispatcher()
    V = [('hiword',) + t for t in hiword.vectors()] + [('extra',) + t for t in pinrun.extra()]
    batches = [V[i:i + size] for i in range(0, len(V), size)]
    lock = threading.Lock(); st = {'builds': {}, 'mixed': 0, 'failedBatches': 0}; bad = []; ran = {'hiword': 0, 'extra': 0}

    def work(bi):
        batch = [t[1:] for t in batches[bi]]; data = battery.encode(batch)
        for t in range(12):
            try:
                r = post(url, [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                               {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': evm.STUB, 'data': '0x' + data.hex()}, 'latest', {evm.STUB: {'code': '0x' + code.hex()}}]},
                               {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}])
                r = {x['id']: x for x in r}
                a, b = r[1].get('result'), r[3].get('result'); res = bytes.fromhex(r[2]['result'][2:])
            except Exception as e:
                time.sleep(2 + t); continue
            if len(res) != 32 * len(batch): time.sleep(1); continue
            exp = battery.expected(batch, data); mm = []
            for k, (tup, e) in enumerate(zip(batch, exp)):
                g = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                if g != e: mm.append({'set': batches[bi][k][0], 'op': tup[0], 'a': hex(tup[1]), 'b': hex(tup[2]), 'c': hex(tup[3]), 'got': hex(g), 'want': hex(e)})
            with lock:
                key = a if a == b else 'MIXED ' + str(a) + ' | ' + str(b)
                if a != b: st['mixed'] += 1
                st['builds'][key] = st['builds'].get(key, 0) + len(batch)
                bad.extend(mm)
                for x in batches[bi]: ran[x[0]] += 1
            return
        with lock: st['failedBatches'] += 1

    with cf.ThreadPoolExecutor(threads) as ex: list(ex.map(work, range(len(batches))))
    res = {'url': url, 'vectors': len(V), 'ran': ran, 'mismatchCount': len(bad), 'mismatches': bad[:200], **st, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'mismatches'}, indent=1))

if __name__ == '__main__':
    main()
