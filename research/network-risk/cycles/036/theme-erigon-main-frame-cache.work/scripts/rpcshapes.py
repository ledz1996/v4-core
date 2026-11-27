"""Task 3: the reentry scenarios of pmshapes.py (same seed, so the same scripts) sent by
eth_call with state overrides to a public erigon 3.8.x endpoint (the frame slot cache ships
from v3.8.0) and to non-erigon control endpoints; each answer is compared with the
reference interpreter's. Read-only calls only. Each batch is bracketed with
web3_clientVersion. Usage: PM_BUILD=... python3 -I rpcshapes.py <out.json> <n> <url> [url ...]"""
import sys, os, json, random, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc
import pmdiff as P
import pmshapes as X


def overrides(pm, hook):
    ov = {}
    for a, c in X.codes(pm, hook).items():
        ov['0x' + a.to_bytes(20, 'big').hex()] = {'code': '0x' + c.hex()}
    ov['0x' + X.PMI.to_bytes(20, 'big').hex()].update({'balance': hex(10 ** 19), 'stateDiff': {'0x' + '00' * 32: '0x' + X.DRV.to_bytes(32, 'big').hex()}})
    return ov


def ask(url, data, ov):
    tx = {'from': '0x' + '00' * 19 + '01', 'to': '0x' + X.DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(30_000_000)}
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [tx, 'latest', ov]}
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    from evm import _ctx
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90, context=_ctx) as r: j = json.load(r)
            break
        except Exception as e:
            j = {'transport': str(e)[:200]}; time.sleep(2 + 3 * k)
    if 'error' in j:  # a reverting call: the record is the revert data
        d = j['error'].get('data')
        return ('revert', bytes.fromhex(d[2:]) if isinstance(d, str) and d.startswith('0x') else None, j['error'].get('message', '')[:200])
    if 'result' in j: return ('ok', bytes.fromhex(j['result'][2:]), '')
    return ('transport', None, json.dumps(j)[:200])


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]); urls = sys.argv[3:]
    pm = P.fetch_code(); rnd = random.Random(36_2026_11_27 + 1)
    scen = [X.scenario(rnd, i) for i in range(n)]
    res = {'seed': 36_2026_11_27 + 1, 'n': n, 'pmCodeSha256': hashlib.sha256(pm).hexdigest(), 'endpoints': {}}
    refs = []
    for desc, data, hook in scen:
        rw, ok, ret = X.run(X.RefWorld, pm, hook, data); refs.append((ok, ret))
    for url in urls:
        e = {'clientBefore': None, 'clientAfter': None, 'agree': 0, 'differ': 0, 'noAnswer': 0, 'records': []}
        try: e['clientBefore'] = rpc(url, 'web3_clientVersion', [])
        except Exception as ex: e['clientBefore'] = 'ERR ' + str(ex)[:200]
        e['startedUtc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        for (desc, data, hook), (ok, ref) in zip(scen, refs):
            kind, got, msg = ask(url, data, overrides(pm, hook))
            r = {'desc': desc, 'kind': kind, 'msg': msg, 'refSha256': hashlib.sha256(ref).hexdigest(), 'gotSha256': hashlib.sha256(got).hexdigest() if got is not None else None}
            if got is None: e['noAnswer'] += 1
            elif got == ref and kind == ('ok' if ok else 'revert'): e['agree'] += 1
            else:
                e['differ'] += 1; r['ref'] = ref.hex(); r['got'] = got.hex(); r['data'] = data.hex(); r['hook'] = hook.hex()
            e['records'].append(r)
            time.sleep(0.3)
        e['endedUtc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        try: e['clientAfter'] = rpc(url, 'web3_clientVersion', [])
        except Exception as ex: e['clientAfter'] = 'ERR ' + str(ex)[:200]
        res['endpoints'][url] = e
        print(url, e['clientBefore'], '->', e['clientAfter'], 'agree', e['agree'], 'differ', e['differ'], 'noAnswer', e['noAnswer'])
    json.dump(res, open(out, 'w'), indent=1)
