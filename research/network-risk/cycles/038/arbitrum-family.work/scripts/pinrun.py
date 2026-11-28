"""Cycle 37 theme-rotating-endpoint-build-pins. Read-only.
Sends opcode vector chunks and PoolManager scripts to one endpoint, each request a JSON-RPC batch
[web3_clientVersion, eth_call x K, web3_clientVersion], and resends a job until every build named in
--builds (or every build seen so far, if none given) has answered it at least once with both brackets equal.
A batch whose two brackets differ is counted as 'mixed' and its results are kept apart.

Sets (seeds as in the source scripts):
  ops       battery.py (seed 20261124) + targeted.py (seed 681) vectors whose op is MULMOD, ADDMOD, DIV, SDIV, MOD,
            SMOD, EXP, SHL, SHR, SAR, BYTE, SIGNEXTEND, DIVUP or MULDIV512
  provevec  cycles/036/arbitrum-family.work/scripts/provevec.py vectors (seed 20261127)
  opsdms    the DIV, SDIV, MOD, SMOD, DIVUP, MULMOD, MULDIV512, SHL, SHR and SAR part of ops
  pmdiff    tools/opdiff/pmdiff.py 250 scripts (seed 7_2026_11_24), deployed Ethereum PoolManager code
  pmdiff2   tools/opdiff/pmdiff2.py 300 scripts (seed 11_2026_11_24)
Script answers are compared with referenceHashes stored in opcodes/pmdiff.json and opcodes/pmdiff2.json.

Usage: python3 -I pinrun.py <url> <set> <out.json> [--builds b1,b2,...] [--threads N] [--max-tries N] [--rounds N]
--size N --per K: vectors per eth_call and eth_calls per batch for vector sets.
--rounds N (per-item routing endpoints): send every job N times without build tracking.
"""
import sys, os, json, time, ssl, random, hashlib, urllib.request, urllib.error, concurrent.futures as cf, threading
R = '/home/user/v4-core/research/network-risk'
T = R + '/tools/opdiff'
sys.path.insert(0, T)
import battery as B, targeted
from evm import STUB, MASK
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
SUB = {'MULMOD', 'ADDMOD', 'DIV', 'SDIV', 'MOD', 'SMOD', 'EXP', 'SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND', 'DIVUP', 'MULDIV512'}


def provevec_vectors():
    src = open(R + '/cycles/036/arbitrum-family.work/scripts/provevec.py').read()
    src = src.split('code = B.dispatcher()')[0].split('from evm import rpc, MASK')[1]
    g = {'random': random, 'MASK': MASK}
    exec(src, g)
    return g['V']


def vec_jobs(V, size=600, per=2):
    code = B.dispatcher(); jobs = []
    chunks = [V[i:i + size] for i in range(0, len(V), size)]
    for j in range(0, len(chunks), per):
        items = []
        for ch in chunks[j:j + per]:
            data = B.encode(ch)
            items.append(({'to': STUB, 'data': '0x' + data.hex()}, {STUB: {'code': '0x' + code.hex()}}, ('vec', ch, data)))
        jobs.append(items)
    return jobs


def script_jobs(which, per=4):
    import pmdiff as P
    if which == 'pmdiff':
        rnd = random.Random(7_2026_11_24); scripts = [P.script(rnd) for _ in range(250)]
        code = P.fetch_code(); drv = P.driver()
        ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}
        ref = json.load(open(R + '/opcodes/pmdiff.json'))['referenceHashes']
    else:
        import pmdiff2 as Q
        rnd = random.Random(11_2026_11_24); scripts = [Q.script(rnd, i) for i in range(300)]
        code = P.fetch_code(); drv = Q.driver(); tok = Q.token(); hk = Q.hook()
        ov = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + drv.hex()},
              '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + tok.hex()}}
        for f in Q.HOOK_FLAGS: ov['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + hk.hex()}
        ref = json.load(open(R + '/opcodes/pmdiff2.json'))['referenceHashes']
    items = [({'to': P.DRV, 'data': '0x' + d.hex(), 'gas': hex(25_000_000)}, ov, ('script', i, ref[i])) for i, (d, _, _) in enumerate(scripts)]
    return [items[i:i + per] for i in range(0, len(items), per)], hashlib.sha256(code).hexdigest()


def send(url, items):
    body = [{'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []}]
    for k, (tx, ov, _) in enumerate(items):
        body.append({'jsonrpc': '2.0', 'id': k + 1, 'method': 'eth_call', 'params': [tx, 'latest', ov]})
    body.append({'jsonrpc': '2.0', 'id': 999, 'method': 'web3_clientVersion', 'params': []})
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
        j = json.load(r)
    if not isinstance(j, list):
        raise RuntimeError('non-batch answer ' + json.dumps(j)[:200])
    j = {x.get('id'): x for x in j}
    return j[0].get('result'), j[999].get('result'), [j.get(k + 1, {}) for k in range(len(items))]


def check(items, answers):
    """returns (#units checked, mismatches, per-op counts, errors)"""
    n = 0; mm = []; ops = {}; errs = []
    for (tx, ov, meta), a in zip(items, answers):
        if 'result' not in a:
            errs.append(json.dumps(a.get('error', a))[:200]); continue
        res = bytes.fromhex(a['result'][2:])
        if meta[0] == 'vec':
            _, ch, data = meta
            if len(res) != 32 * len(ch):
                errs.append('short %d' % len(res)); continue
            exp = B.expected(ch, data)
            for k, (t, e) in enumerate(zip(ch, exp)):
                got = int.from_bytes(res[32 * k:32 * k + 32], 'big'); n += 1; ops[t[0]] = ops.get(t[0], 0) + 1
                if got != e:
                    mm.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
        else:
            _, i, ref = meta; h = hashlib.sha256(res).hexdigest(); n += 1
            if h != ref:
                mm.append({'script': i, 'gotSha256': h, 'refSha256': ref, 'answer': a['result']})
    return n, mm, ops, errs


def main():
    a = sys.argv[1:]; url, setname, out = a[0], a[1], a[2]
    opt = {a[i]: a[i + 1] for i in range(3, len(a) - 1, 2)}
    want = set(opt['--builds'].split(',')) if '--builds' in opt else None
    th = int(opt.get('--threads', 3)); maxt = int(opt.get('--max-tries', 60)); rounds = int(opt.get('--rounds', 0))
    meta = {}
    if setname == 'ops':
        V = [v for v in B.vectors() + targeted.vectors() if v[0] in SUB]; jobs = vec_jobs(V, size=int(opt.get('--size', 600)), per=int(opt.get('--per', 2))); meta['vectors'] = len(V)
    elif setname == 'opsdms':  # division, MULMOD and shift subset only (Task 4)
        D = {'DIV', 'SDIV', 'MOD', 'SMOD', 'DIVUP', 'MULMOD', 'MULDIV512', 'SHL', 'SHR', 'SAR'}
        V = [v for v in B.vectors() + targeted.vectors() if v[0] in D]; jobs = vec_jobs(V, size=int(opt.get('--size', 600)), per=int(opt.get('--per', 2))); meta['vectors'] = len(V)
    elif setname == 'provevec':
        V = provevec_vectors(); jobs = vec_jobs(V, size=int(opt.get('--size', 400)), per=int(opt.get('--per', 3))); meta['vectors'] = len(V)
    else:
        jobs, sha = script_jobs(setname); meta['scripts'] = sum(len(j) for j in jobs); meta['pmCodeSha256'] = sha
    lock = threading.Lock()
    by = {}; mism = []; errors = []; refusals = []; seen = set(); tries = {}
    stop = threading.Event()

    def work(ji):
        items = jobs[ji]; got = set(); t = 0
        target_rounds = rounds if rounds else None
        while not stop.is_set():
            if target_rounds is not None and t >= target_rounds: break
            if target_rounds is None:
                need = (want or seen) - got
                if got and not need and (want or t >= 3): break
                if t >= maxt: break
            t += 1
            try:
                v1, v2, ans = send(url, items)
            except urllib.error.HTTPError as e:
                with lock: refusals.append({'job': ji, 'http': e.code, 'body': e.read()[:200].decode('latin1')})
                if e.code in (403, 429):
                    if sum(1 for r in refusals if r['http'] in (403, 429)) > 2000: stop.set()
                    time.sleep(15)
                continue
            except Exception as e:  # noqa
                with lock: errors.append({'job': ji, 'err': str(e)[:200]})
                time.sleep(3); continue
            key = v1 if v1 == v2 else 'mixed:%s|%s' % (v1, v2)
            n, mm, ops, errs = check(items, ans)
            with lock:
                if v1 == v2: seen.add(v1)
                s = by.setdefault(key, {'batches': 0, 'units': 0, 'mismatches': 0, 'perOp': {}, 'jobs': set(), 'callErrors': 0})
                s['batches'] += 1; s['units'] += n; s['mismatches'] += len(mm); s['callErrors'] += len(errs)
                for k, c in ops.items(): s['perOp'][k] = s['perOp'].get(k, 0) + c
                if not errs: s['jobs'].add(ji)
                mism.extend(dict(m, build=key, job=ji) for m in mm)
                if errs: errors.append({'job': ji, 'build': key, 'callErrors': errs[:3]})
            if v1 == v2 and not errs: got.add(v1)
        with lock: tries[ji] = t

    t0 = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with cf.ThreadPoolExecutor(th) as ex:
        list(ex.map(work, range(len(jobs))))
    full = {k: (len(v['jobs']) == len(jobs)) for k, v in by.items()}
    for v in by.values(): v['jobsComplete'] = len(v['jobs']); v['jobs'] = None
    r = {'url': url, 'set': setname, 'start': t0, 'end': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'meta': meta,
         'jobs': len(jobs), 'itemsPerJob': len(jobs[0]), 'wantBuilds': sorted(want) if want else None, 'byBuild': by,
         'fullSetPerBuild': full, 'mismatchCount': len(mism), 'mismatches': mism, 'errors': errors[:100],
         'errorCount': len(errors), 'refusals': refusals[:50], 'refusalCount': len(refusals),
         'triesTotal': sum(tries.values()), 'stoppedOnRefusals': stop.is_set()}
    json.dump(r, open(out, 'w'), indent=1)
    print(json.dumps({'url': url, 'set': setname, 'jobs': len(jobs), 'mismatches': len(mism), 'errors': len(errors), 'refusals': len(refusals),
                      'byBuild': {k: [v['batches'], v['units'], v['mismatches'], v['jobsComplete']] for k, v in by.items()}, 'full': full}, indent=1))


if __name__ == '__main__':
    main()
