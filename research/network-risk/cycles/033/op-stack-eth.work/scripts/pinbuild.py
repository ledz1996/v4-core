"""Run the battery and targeted vectors several rounds on OP Mainnet's load-balanced
endpoint, which routes every request (and every item of a batch) to one of two builds
on its own. Each request is a batch [web3_clientVersion, eth_call(chunk), web3_clientVersion];
the version answers only sample the share of each build, since a batch is split.
Every chunk's answer is checked against the reference in every round.
Read-only eth_call only.

Usage: python3 -I pinbuild.py <tools/opdiff dir> <url> <out.json> [rounds]
"""
import sys, json, urllib.request, ssl, time
sys.path.insert(0, sys.argv[1])
from evm import STUB  # noqa
import battery, targeted

url, out = sys.argv[2], sys.argv[3]
rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 1
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
code = battery.dispatcher()
V = battery.vectors() + targeted.vectors()


def batch(data):
    tx = {'to': STUB, 'data': '0x' + data.hex()}
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [tx, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
        j = json.load(r)
    j = {x['id']: x for x in j}
    return j[1].get('result'), j[3].get('result'), j[2]


per = {}; share = {}; errs = []
for rnd in range(rounds):
    for i in range(0, len(V), 600):
        ch = V[i:i + 600]; data = battery.encode(ch)
        try:
            v1, v2, r = batch(data)
        except Exception as e:  # noqa
            errs.append((i, str(e)[:120])); time.sleep(2); continue
        share[v1] = share.get(v1, 0) + 1; share[v2] = share.get(v2, 0) + 1
        b = per.setdefault('all', {'chunks': 0, 'vectors': 0, 'mismatches': [], 'errors': 0})
        if 'result' not in r:
            b['errors'] += 1; continue
        res = bytes.fromhex(r['result'][2:]); exp = battery.expected(ch, data)
        b['chunks'] += 1; b['vectors'] += len(ch)
        for k, (t, e) in enumerate(zip(ch, exp)):
            got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
            if got != e:
                b['mismatches'].append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
    print('round', rnd, {k: (v['vectors'], len(v['mismatches'])) for k, v in per.items()}, 'share', share, 'errors', len(errs), flush=True)
json.dump({'url': url, 'vectorsPerRound': len(V), 'rounds': rounds, 'perBuild': per, 'versionSamples': share, 'errors': errs[:20]}, open(out, 'w'), indent=1)
