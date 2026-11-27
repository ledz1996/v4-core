"""Cycle 28 op-stack-custom-gas: run opcode vector sets on one endpoint, each eth_call sent
inside a JSON-RPC batch [web3_clientVersion, eth_call, web3_clientVersion] and kept only when
both version strings contain the wanted build. Read-only (eth_call with a code override).
Sets: battery, targeted, extra (cycle 27 pinrun.py, 14,598), hiword (cycle 27 hiword.py, 15,510).
Usage: python3 pinbatch.py <out.json> <url> <build substring> <sets> [size] [tries] [threads]"""
import sys, json, time, threading, urllib.request, collections, concurrent.futures as cf
R = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, R + '/tools/opdiff'); sys.path.insert(0, R + '/cycles/027/ethereum-reference.work'); sys.path.insert(0, R + '/cycles/027/op-stack-eth.work/scripts')
import evm, battery, targeted, pinrun, hiword

def main():
    out, url, want, sets = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
    size = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    tries = int(sys.argv[6]) if len(sys.argv) > 6 else 80
    thr = int(sys.argv[7]) if len(sys.argv) > 7 else 4
    code = battery.dispatcher(); V = []
    if 'battery' in sets: V += battery.vectors()
    if 'targeted' in sets: V += targeted.vectors()
    if 'extra' in sets: V += pinrun.extra()
    if 'hiword' in sets: V += hiword.vectors()
    batches = [V[i:i + size] for i in range(0, len(V), size)]
    st = collections.Counter(); bad = []; lock = threading.Lock()
    import os; PROG = os.environ.get('PINBATCH_PROGRESS')
    def work(bi):
        batch = batches[bi]; data = battery.encode(batch)
        body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': evm.STUB, 'data': '0x' + data.hex()}, 'latest', {evm.STUB: {'code': '0x' + code.hex()}}]},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]).encode()
        for t in range(tries):
            try:
                req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
                with urllib.request.urlopen(req, timeout=120, context=evm._ctx) as r:
                    j = {x['id']: x for x in json.load(r)}
            except Exception as e:
                with lock: st['transport'] += 1
                time.sleep(2 + t % 7); continue
            v1, v3 = str(j.get(1, {}).get('result', '')), str(j.get(3, {}).get('result', ''))
            with lock: st['seen:' + v1] += 1
            if want not in v1 or want not in v3 or 'result' not in j.get(2, {}):
                with lock: st['skip'] += 1
                if 'error' in j.get(2, {}): time.sleep(2)
                continue
            res = bytes.fromhex(j[2]['result'][2:])
            if len(res) != 32 * len(batch):
                with lock: st['badlen'] += 1
                continue
            exp = battery.expected(batch, data); mm = []
            for k, (tup, e) in enumerate(zip(batch, exp)):
                g = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                if g != e: mm.append({'op': tup[0], 'a': hex(tup[1]), 'b': hex(tup[2]), 'c': hex(tup[3]), 'got': hex(g), 'want': hex(e)})
            with lock:
                st['pinned'] += 1; bad.extend(mm); st['vectorsPinned'] += len(batch)
                if PROG: json.dump({'build': want, 'vectors': len(V), 'progress': dict(st), 'mismatchCount': len(bad), 'mismatches': bad[:50]}, open(PROG, 'w'))
            return len(batch)
        with lock: st['unpinned'] += 1
        return 0
    with cf.ThreadPoolExecutor(thr) as ex: ran = sum(ex.map(work, range(len(batches))))
    r = {'url': url, 'build': want, 'sets': sets, 'vectors': len(V), 'batches': len(batches), 'ranPinned': ran, 'mismatchCount': len(bad), 'mismatches': bad[:200], 'stats': dict(st)}
    json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'}, indent=1))

if __name__ == '__main__': main()
