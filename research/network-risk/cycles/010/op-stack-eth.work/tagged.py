"""Lead L-616. Run the battery and targeted vectors on OP Mainnet with every chunk sent
as one JSON-RPC batch [web3_clientVersion, eth_call], so each answer is tagged with the
version string of the backend that answered in the same HTTP request. Also records the
x-proxyd-cache-status header. Read only: eth_call with a state override.

Usage: python3 tagged.py <out.json> [url]
"""
import sys, os, json, time, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
import battery, targeted
from evm import STUB, _ctx

URL = sys.argv[2] if len(sys.argv) > 2 else 'https://mainnet.optimism.io'


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=90, context=_ctx) as r:
        return json.load(r), r.headers.get('x-proxyd-cache-status')


def run(name, V, code, size=600):
    out = []
    for i in range(0, len(V), size):
        batch = V[i:i + size]; data = battery.encode(batch)
        body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': STUB, 'data': '0x' + data.hex()}, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
        rec = {'set': name, 'start': i, 'n': len(batch)}
        for k in range(3):
            try:
                j, cache = post(body); break
            except Exception as e:  # noqa
                j = None; rec['error'] = str(e)[:160]; time.sleep(2 * (k + 1))
        if j is None:
            out.append(rec); continue
        byid = {x.get('id'): x for x in j} if isinstance(j, list) else {}
        rec['versionBefore'] = byid.get(1, {}).get('result'); rec['versionAfter'] = byid.get(3, {}).get('result'); rec['cache'] = cache
        res = byid.get(2, {})
        if 'result' not in res:
            rec['error'] = json.dumps(res.get('error', res))[:200]; out.append(rec); continue
        got = bytes.fromhex(res['result'][2:]); exp = battery.expected(batch, data)
        bad = [k for k in range(len(batch)) if int.from_bytes(got[32 * k:32 * k + 32], 'big') != exp[k]] if len(got) == 32 * len(batch) else list(range(len(batch)))
        rec['mismatches'] = len(bad); rec['firstBad'] = [list(map(str, batch[k])) for k in bad[:5]]
        out.append(rec)
    return out


if __name__ == '__main__':
    code = battery.dispatcher()
    recs = run('battery', battery.vectors(), code) + run('targeted', targeted.vectors(), code)
    summ = {}
    for r in recs:
        v = (r.get('versionBefore'), r.get('versionAfter'))
        s = summ.setdefault(' | '.join(map(str, v)), {'chunks': 0, 'vectors': 0, 'mismatches': 0, 'errors': 0})
        if 'mismatches' in r:
            s['chunks'] += 1; s['vectors'] += r['n']; s['mismatches'] += r['mismatches']
        else:
            s['errors'] += 1
    json.dump({'url': URL, 'summary': summ, 'records': recs}, open(sys.argv[1], 'w'), indent=1)
    print(json.dumps(summ, indent=1))
