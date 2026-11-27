"""Cycle 29 ethereum-reference, lead L-1180 part 2: the 23 multi-transaction scenarios of
cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py, run on Ethereum endpoints with eth_simulateV1
(one simulated block, one call per scenario transaction, state carried from call to call and transient storage
cleared between them, as between transactions), with the same codes and PoolManager storage the reference uses
(scen28.ref, pyevm.py). A last call reads, with extsload(bytes32[]), every PoolManager slot the reference leaves
nonzero. Every call's status and return data and the final slots are compared with the reference word for word.
The request is a batch [web3_clientVersion, eth_simulateV1, web3_clientVersion]. Read-only.
Usage: python3 simscen.py <out.json> <url> [...]"""
import sys, os, json, urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts')
import scen28 as S
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def post(url, body, timeout=300):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r: return json.loads(r.read())
# per-call gas for endpoints whose gas cap is about 50 million (the block total must stay under it)
GAS = {'https://ethereum-rpc.publicnode.com': 2_400_000}
def h(a): return '0x%040x' % a
def main():
    out, urls = sys.argv[1], sys.argv[2:]
    res = {'pm': hex(S.PM), 'scenarios': {}}
    for nm, sc in S.SCEN.items():
        ref_outs, ref_st = S.ref(sc)
        cs = S.codes_for(S.PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
        ov = {h(a): {'code': '0x' + c.hex()} for a, c in cs.items()}
        if sc['storage']: ov[h(S.PM)]['stateDiff'] = {'0x%064x' % int(k, 16): '0x%064x' % int(v, 16) for k, v in sc['storage'].items()}
        keys = sorted(ref_st, key=lambda k: int(k, 16))
        want_st = [int(ref_st[k], 16) for k in keys]
        r = {'ntx': len(sc['txs']), 'refSlots': len(keys), 'urls': {}}
        for url in urls:
            e = {}
            g = GAS.get(url, 25_000_000)
            calls = [{'from': h(S.EOA), 'to': h(S.addr(t['to'])), 'data': '0x' + t['data'], 'gas': hex(g)} for t in sc['txs']]
            calls.append({'from': h(S.EOA), 'to': h(S.PM), 'data': '0x' + S.ext_arr([int(k, 16) for k in keys]).hex(), 'gas': hex(2_000_000)})
            try:
                body = [{'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []},
                        {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'blockOverrides': {'gasLimit': hex(g * len(calls) + 2_000_000)}, 'stateOverrides': ov, 'calls': calls}]}, 'latest']},
                        {'jsonrpc': '2.0', 'id': 2, 'method': 'web3_clientVersion', 'params': []}]
                m = {x['id']: x for x in post(url, body)}
                e['before'], e['after'] = m[0].get('result'), m[2].get('result')
                if 'result' not in m[1]: e['error'] = str(m[1].get('error'))[:300]
                else:
                    cr = m[1]['result'][0]['calls']; diffs = []
                    for i, ((rok, rret), c) in enumerate(zip(ref_outs, cr)):
                        ok = c.get('status') == '0x1'; ret = (c.get('returnData') or '0x')[2:]
                        if not ok and not ret: ret = ((c.get('error') or {}).get('data') or '0x')[2:]  # eth_simulateV1 puts revert data in error.data
                        if ok != rok: diffs.append(f'tx {i} status ref={rok} got={ok} err={str(c.get("error"))[:120]}')
                        elif ret != rret: diffs.append(f'tx {i} returnData differs')
                    last = cr[-1]; b = bytes.fromhex((last.get('returnData') or '0x')[2:])
                    got = [int.from_bytes(b[64 + 32 * i:96 + 32 * i], 'big') for i in range(len(keys))]
                    if last.get('status') != '0x1' or got != want_st: diffs.append('final PoolManager slots differ')
                    e['calls'] = len(cr); e['diffs'] = diffs; e['equal'] = not diffs
            except Exception as x: e['error'] = repr(x)[:300]
            e['gasPerCall'] = g; r['urls'][url] = e
            print(nm[:60], url.split('/')[2], {k: v for k, v in e.items() if k != 'diffs'}, e.get('diffs', [])[:3], flush=True)
        res['scenarios'][nm] = r
    json.dump(res, open(out, 'w'), indent=1)
if __name__ == '__main__': main()
