"""Cycle 32: battery.py and targeted.py vectors against one Celo endpoint, each eth_call sent in one
JSON-RPC batch between two web3_clientVersion calls, so every result is tied to the build that answered it.
Read-only: eth_call with a code override at an unused address. Usage: pinned.py <url> <out.json> [threads]"""
import sys, os, json, time, ssl, urllib.request, concurrent.futures as cf
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import battery, targeted
from evm import STUB

ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')


def batch_call(url, code, data):
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': STUB, 'data': '0x' + data.hex()}, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
        j = {x['id']: x for x in json.load(r)}
    v1, v3 = j[1].get('result'), j[3].get('result')
    if 'error' in j[2]:
        raise RuntimeError(json.dumps(j[2]['error'])[:200])
    return v1, v3, bytes.fromhex(j[2]['result'][2:])


def main():
    url, out = sys.argv[1], sys.argv[2]
    th = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    sets = [('battery', battery.dispatcher(), battery.vectors(), battery.expected, battery.encode)]
    tv = targeted.vectors() if hasattr(targeted, 'vectors') else None
    if tv is not None:
        sets.append(('targeted', battery.dispatcher(), tv, battery.expected, battery.encode))
    jobs = []
    for name, code, V, exp, enc in sets:
        for i in range(0, len(V), 600):
            jobs.append((name, code, V[i:i + 600], exp, enc))
    stats = {}
    bad = []; errors = []

    def work(job):
        name, code, b, exp, enc = job
        data = enc(b)
        for k in range(3):
            try:
                v1, v3, res = batch_call(url, code, data)
                break
            except Exception as e:  # noqa
                last = str(e)[:160]; time.sleep(2 * (k + 1))
        else:
            return name, None, len(b), [], last
        if len(res) != 32 * len(b):
            return name, (v1, v3), len(b), [], 'short %d' % len(res)
        e = exp(b, data); mm = []
        for t, w, k in zip(b, e, range(len(b))):
            got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
            if got != w:
                mm.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(w)})
        return name, (v1, v3), len(b), mm, None

    with cf.ThreadPoolExecutor(th) as ex:
        for name, vv, n, mm, err in ex.map(work, jobs):
            if err:
                errors.append({'set': name, 'err': err, 'versions': vv}); continue
            key = vv[0] if vv[0] == vv[1] else 'mixed:%s|%s' % vv
            s = stats.setdefault(key, {}).setdefault(name, {'batches': 0, 'vectors': 0, 'mismatches': 0})
            s['batches'] += 1; s['vectors'] += n; s['mismatches'] += len(mm)
            bad += [dict(m, build=key, set=name) for m in mm]
    r = {'url': url, 'when': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'jobs': len(jobs), 'byBuild': stats, 'mismatches': bad[:200], 'errors': errors[:40], 'errorCount': len(errors)}
    json.dump(r, open(out, 'w'), indent=1)
    print(json.dumps({k: r[k] for k in ('url', 'jobs', 'byBuild', 'errorCount')}, indent=1))


if __name__ == '__main__':
    main()
