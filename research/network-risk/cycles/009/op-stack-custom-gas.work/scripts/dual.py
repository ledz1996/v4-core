"""Run the opdiff tools against one endpoint that load balances several clients, and make
every eth_call answer from each client family. Each request is a JSON-RPC batch of
web3_clientVersion followed by the eth_call, so one backend answers both.

Usage: python3 dual.py <tool> <out.json> <chainId> [extra args]
  tool: battery | targeted | pmdiff | pmdiff2
For pmdiff and pmdiff2 the reference is the stored referenceHashes of
research/network-risk/opcodes/<build->pmdiff*.json (PM_BUILD selects build-).
"""
import sys, os, json, time, hashlib, threading, concurrent.futures as cf, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
OPC = os.path.normpath(os.path.join(TOOLS, '..', '..', 'opcodes'))
sys.path.insert(0, TOOLS)
import evm  # noqa

WANT = set(os.environ.get('DUAL_WANT', 'reth,Geth').split(','))
MAXTRY = int(os.environ.get('DUAL_MAXTRY', 80))
PAR = int(os.environ.get('DUAL_PAR', 6))
LOG = {'calls': 0, 'perClient': {}, 'disagree': [], 'incomplete': 0, 'attempts': 0}
LK = threading.Lock()
orig_rpc = evm.rpc


def one(url, method, params, timeout):
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params}]
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=evm._ctx) as r:
        j = json.load(r)
    j = {x['id']: x for x in j}
    cv = j[1].get('result', '?')
    fam = cv.split('/')[0]
    res = j[2]
    return fam, cv, ('R', res['result']) if 'result' in res else ('E', json.dumps(res.get('error'))[:200])


def dual_rpc(url, method, params, timeout=60):
    if method != 'eth_call':
        return orig_rpc(url, method, params, timeout)
    got = {}; versions = {}; tries = 0
    while tries < MAXTRY and not WANT <= set(got):
        with cf.ThreadPoolExecutor(PAR) as ex:
            futs = [ex.submit(one, url, method, params, timeout) for _ in range(PAR)]
            for f in futs:
                try:
                    fam, cv, r = f.result()
                except Exception:
                    continue
                if fam not in got: got[fam] = r; versions[fam] = cv
                elif got[fam] != r:
                    with LK: LOG['disagree'].append({'sameClient': fam, 'a': str(got[fam])[:80], 'b': str(r)[:80]})
        tries += PAR
    with LK:
        LOG['calls'] += 1; LOG['attempts'] += tries
        for fam, cv in versions.items(): LOG['perClient'][cv] = LOG['perClient'].get(cv, 0) + 1
        if not WANT <= set(got): LOG['incomplete'] += 1
        vals = set(got.values())
        if len(vals) > 1:
            LOG['disagree'].append({fam: str(v)[:200] for fam, v in got.items()} | {'params': json.dumps(params[0])[:200]})
    if not got: raise RuntimeError('no answer')
    k = 'reth' if 'reth' in got else sorted(got)[0]
    kind, v = got[k]
    if kind == 'E': raise RuntimeError(v)
    return v


evm.rpc = dual_rpc

if __name__ == '__main__':
    tool, out, cid = sys.argv[1], sys.argv[2], int(sys.argv[3])
    nets = [n for n in evm.networks() if n[0] == cid]
    t0 = time.time(); result = {}
    if tool in ('battery', 'targeted'):
        import battery
        battery.call_code.__globals__['rpc'] = dual_rpc
        if tool == 'battery':
            V = battery.vectors()
        else:
            import targeted; V = targeted.vectors()
        code = battery.dispatcher()
        lim = int(os.environ.get('DUAL_LIMIT', len(V)))
        done, bad, errors = battery.run(nets[0][2], code, V[:lim], size=int(os.environ.get('DUAL_SIZE', 600)))
        result = {'tool': tool, 'vectors': lim, 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:20]}
    else:
        import random
        pre = 'build-' if os.environ.get('PM_BUILD') else ''
        if tool == 'pmdiff':
            import pmdiff as M
            rnd = random.Random(7_2026_11_24); n = 250
            scripts = [M.script(rnd) for _ in range(n)]
            M.rpc = dual_rpc
            code = M.fetch_code(); drv = M.driver()
            _, _, res = M.run_net(nets[0], code, drv, scripts)
        else:
            import pmdiff2 as M2, pmdiff as P
            rnd = random.Random(11_2026_11_24); n = 300
            scripts = [M2.script(rnd, i) for i in range(n)]
            M2.rpc = dual_rpc; P.rpc = orig_rpc
            code = P.fetch_code(); drv = M2.driver(); tok = M2.token(); hk = M2.hook()
            ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + drv.hex()},
                  '0x' + M2.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + tok.hex()}}
            for f in M2.HOOK_FLAGS: ov['0x' + (M2.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + hk.hex()}
            _, _, res = M2.run_net(nets[0], ov, scripts)
        ref = json.load(open(os.path.join(OPC, pre + tool + '.json')))['referenceHashes']
        same = sum(1 for a, b in zip(res, ref) if a == b)
        diff = [i for i, (a, b) in enumerate(zip(res, ref)) if a != b and not a.startswith('ERR') and not b.startswith('ERR')]
        result = {'tool': tool, 'build': bool(pre), 'scripts': n, 'identicalToStoredEthereumReference': same, 'different': diff,
                  'errors': sum(1 for a in res if a.startswith('ERR')), 'refErrors': sum(1 for b in ref if b.startswith('ERR'))}
    result['chainId'] = cid; result['rpc'] = nets[0][2]; result['seconds'] = round(time.time() - t0); result['dual'] = LOG
    json.dump(result, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in result.items() if k not in ('mismatches',)})[:1500])
