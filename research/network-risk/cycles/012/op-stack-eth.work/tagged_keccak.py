"""Lead L-661. The cycle 11 keccak bucket test (keccak_buckets.py) on OP Mainnet with every chunk sent
as one JSON-RPC batch [web3_clientVersion, eth_call, web3_clientVersion], retried until both version
entries name the unversioned dev build (up to 8 tries). Every returned word is compared with the
Python keccak. Read only: eth_call with a state override.

Usage: python3 tagged_keccak.py <out.json> [rounds]
"""
import sys, os, json, time, urllib.request
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..', '..', '011', 'theme-keccak-cache.work'))
sys.path.insert(0, os.path.join(here, '..', '..', '..', 'tools', 'opdiff'))
import keccak_buckets as kb
from evm import _ctx, STUB

URL = 'https://mainnet.optimism.io'
WANT = 'op-reth/v0.0.0-dev'


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=120, context=_ctx) as r:
        return json.load(r)


if __name__ == '__main__':
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    recs, meta = kb.build(); code = kb.contract()
    flat = [d for g in recs for d in g]
    chunks = [flat[i:i + 500] for i in range(0, len(flat), 500)]
    out = {'meta': meta, 'records': len(flat), 'rounds': []}
    for r in range(rounds):
        st = {'chunks': 0, 'bracketedChunks': 0, 'bracketedWords': 0, 'bracketedBad': 0, 'otherWords': 0, 'otherBad': 0, 'errors': 0, 'bad': []}
        for ch in chunks:
            data = kb.encode(ch)
            body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                    {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': STUB, 'data': '0x' + data.hex()}, 'latest', {STUB: {'code': '0x' + code.hex()}}]},
                    {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
            st['chunks'] += 1
            for k in range(8):
                try:
                    j = post(body)
                except Exception as e:  # noqa
                    st['errors'] += 1; time.sleep(2); continue
                by = {x.get('id'): x for x in j} if isinstance(j, list) else {}
                vb, va, res = by.get(1, {}).get('result'), by.get(3, {}).get('result'), by.get(2, {}).get('result')
                if not res or len(res) != 2 + 64 * len(ch):
                    st['errors'] += 1; continue
                got = bytes.fromhex(res[2:])
                bad = [d.hex() for i, d in enumerate(ch) if got[32 * i:32 * i + 32] != kb.kc(d)]
                dev = bool(vb and va and vb.startswith(WANT) and va.startswith(WANT))
                if dev:
                    st['bracketedChunks'] += 1; st['bracketedWords'] += len(ch); st['bracketedBad'] += len(bad); st['bad'] += bad[:5]; break
                st['otherWords'] += len(ch); st['otherBad'] += len(bad); st['bad'] += bad[:5]
        out['rounds'].append(st)
        print('round', r, {k: v for k, v in st.items() if k != 'bad'}, flush=True)
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
