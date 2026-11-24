"""Lead L-661. Run the 250 pmdiff.py scripts on OP Mainnet with every script sent as one JSON-RPC
batch [web3_clientVersion, eth_call, web3_clientVersion]. A script is retried until both version
entries of one batch name the requested build (default: the unversioned dev build), up to 8 tries,
and its result hash is compared with the Ethereum reference hash that pmdiff.py stored.
Read only: eth_call with state overrides.

Usage: python3 tagged_pmdiff.py <pmdiff.json with referenceHashes> <out.json> [want-prefix]
"""
import sys, os, json, time, random, hashlib, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
import pmdiff
from evm import _ctx

URL = 'https://mainnet.optimism.io'
WANT = sys.argv[3] if len(sys.argv) > 3 else 'op-reth/v0.0.0-dev'


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=120, context=_ctx) as r:
        return json.load(r)


if __name__ == '__main__':
    ref = json.load(open(sys.argv[1]))['referenceHashes']
    rnd = random.Random(7_2026_11_24)
    scripts = [pmdiff.script(rnd) for _ in range(len(ref))]
    code = pmdiff.fetch_code(); drv = pmdiff.driver()
    ov = {pmdiff.PM: {'code': '0x' + code.hex()}, pmdiff.DRV: {'code': '0x' + drv.hex()}}
    recs = []
    for i, (data, _, _) in enumerate(scripts):
        body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': pmdiff.DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest', ov]},
                {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
        rec = {'script': i, 'tries': []}
        for k in range(8):
            try:
                j = post(body)
            except Exception as e:  # noqa
                rec['tries'].append({'error': str(e)[:120]}); time.sleep(2); continue
            by = {x.get('id'): x for x in j} if isinstance(j, list) else {}
            vb, va = by.get(1, {}).get('result'), by.get(3, {}).get('result')
            res = by.get(2, {}).get('result')
            h = hashlib.sha256(bytes.fromhex(res[2:])).hexdigest() if res else 'ERR'
            rec['tries'].append({'before': vb, 'after': va, 'same': h == ref[i]})
            if vb and va and vb.startswith(WANT) and va.startswith(WANT):
                rec['bracketed'] = True; rec['same'] = h == ref[i]; break
        recs.append(rec)
    br = [r for r in recs if r.get('bracketed')]
    allt = [t for r in recs for t in r['tries'] if 'same' in t]
    summ = {'want': WANT, 'scripts': len(recs), 'bracketed': len(br), 'bracketedSame': sum(1 for r in br if r['same']),
            'allTries': len(allt), 'allTriesSame': sum(1 for t in allt if t['same']),
            'refErrors': sum(1 for h in ref if h.startswith('ERR'))}
    json.dump({'url': URL, 'summary': summ, 'records': recs}, open(sys.argv[2], 'w'), indent=1)
    print(json.dumps(summ))
