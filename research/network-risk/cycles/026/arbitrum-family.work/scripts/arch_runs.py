"""Cycle 26, lead L-1109. Robinhood Chain's load balancer routes every JSON-RPC request
(and every element of a batch) to an amd64 or an arm64 backend independently, so a
bracket of web3_clientVersion cannot pin one eth_call to one architecture.

This driver therefore repeats every batch REPEAT times. Each repeat is bracketed by
web3_clientVersion before and after; the bracket pair is recorded with the answer.
Every answer of every repeat is checked against the specified word (battery,
targeted) or against the Ethereum reference hash recorded in cycle 25 (pmdiff, same
seed 7_2026_11_24 and same PoolManager code sha256). Because routing is independent
per request, a batch that no repeat sent to amd64 has probability 2^-REPEAT; the
count of repeats whose two brackets both said amd64 (or arm64) is reported per batch.

Usage: python3 arch_runs.py <set: battery|targeted|pmdiff> <out.json> [repeat]
"""
import sys, os, json, time, hashlib, random
HERE = os.path.dirname(os.path.abspath(__file__))
OPD = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, OPD)
import evm
from evm import rpc, call_code

URL = 'https://rpc.mainnet.chain.robinhood.com'


def arch():
    try:
        v = rpc(URL, 'web3_clientVersion', [], timeout=30)
        return 'amd64' if 'amd64' in v else ('arm64' if 'arm64' in v else v)
    except Exception as e:  # noqa
        return 'ERR ' + str(e)[:60]


def main():
    which, out = sys.argv[1], sys.argv[2]
    rep = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    t0 = time.time()
    log = {'set': which, 'url': URL, 'repeat': rep, 'startClientVersion': rpc(URL, 'web3_clientVersion', []),
           'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'batches': []}
    mism = []
    if which in ('battery', 'targeted'):
        import battery
        if which == 'battery':
            V = battery.vectors()
        else:
            import targeted
            V = targeted.vectors()
        code = battery.dispatcher(); size = 600
        log['vectors'] = len(V)
        for i in range(0, len(V), size):
            batch = V[i:i + size]; data = battery.encode(batch); exp = battery.expected(batch, data)
            rec = {'start': i, 'n': len(batch), 'runs': []}
            for r in range(rep):
                a1 = arch()
                try:
                    res = call_code(URL, code, data)
                    err = None
                except Exception as e:  # noqa
                    res = b''; err = str(e)[:120]
                a2 = arch()
                bad = 0
                if err is None and len(res) == 32 * len(batch):
                    for k, (t, e) in enumerate(zip(batch, exp)):
                        got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
                        if got != e:
                            bad += 1
                            mism.append({'batch': i, 'repeat': r, 'brackets': [a1, a2], 'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
                elif err is None:
                    err = f'short answer {len(res)}'
                rec['runs'].append({'brackets': [a1, a2], 'mismatches': bad, 'error': err})
            log['batches'].append(rec)
            print(i, [x['brackets'] for x in rec['runs']], sum(x['mismatches'] for x in rec['runs']), flush=True)
    else:
        os.environ['PM_BUILD'] = os.path.join(OPD, '..', '..', 'build', 'PoolManager.json')
        import pmdiff
        ref = json.load(open(os.path.join(HERE, '..', '..', '..', '025', 'arbitrum-family.work', 'raw', 'pmdiff.json')))
        rnd = random.Random(7_2026_11_24)
        n = ref['scripts']
        scripts = [pmdiff.script(rnd) for _ in range(n)]
        code = pmdiff.fetch_code(); drv = pmdiff.driver()
        sha = hashlib.sha256(code).hexdigest()
        log['poolManagerCodeSha256'] = sha
        log['cycle25Sha256'] = ref['poolManagerCodeSha256']
        assert sha == ref['poolManagerCodeSha256'], 'code differs from cycle 25 run'
        ov = {pmdiff.PM: {'code': '0x' + code.hex()}, pmdiff.DRV: {'code': '0x' + drv.hex()}}
        for idx, (data, _, _) in enumerate(scripts):
            rec = {'script': idx, 'runs': []}
            for r in range(rep):
                a1 = arch(); h = None; err = None
                for k in range(3):
                    try:
                        res = rpc(URL, 'eth_call', [{'to': pmdiff.DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest', ov], timeout=90)
                        h = hashlib.sha256(bytes.fromhex(res[2:])).hexdigest(); err = None; break
                    except Exception as e:  # noqa
                        err = str(e)[:120]; time.sleep(2)
                a2 = arch()
                same = (h == ref['referenceHashes'][idx])
                if not same:
                    mism.append({'script': idx, 'repeat': r, 'brackets': [a1, a2], 'hash': h, 'ref': ref['referenceHashes'][idx], 'error': err})
                rec['runs'].append({'brackets': [a1, a2], 'identical': same, 'error': err})
            log['batches'].append(rec)
            print(idx, [x['brackets'] for x in rec['runs']], all(x['identical'] for x in rec['runs']), flush=True)
    # coverage summary
    both_amd = sum(1 for b in log['batches'] if any(x['brackets'] == ['amd64', 'amd64'] for x in b['runs']))
    both_arm = sum(1 for b in log['batches'] if any(x['brackets'] == ['arm64', 'arm64'] for x in b['runs']))
    any_amd = sum(1 for b in log['batches'] if any('amd64' in x['brackets'] for x in b['runs']))
    log['summary'] = {'batches': len(log['batches']), 'batchesWithAmd64AmdBracketedRun': both_amd,
                      'batchesWithArm64ArmBracketedRun': both_arm, 'batchesWithAnyAmd64Bracket': any_amd,
                      'mismatchCount': len(mism), 'errors': sum(1 for b in log['batches'] for x in b['runs'] if x.get('error')),
                      'seconds': round(time.time() - t0)}
    log['mismatches'] = mism
    log['endClientVersion'] = rpc(URL, 'web3_clientVersion', [])
    log['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(log, open(out, 'w'), indent=1)
    print(json.dumps(log['summary']))


if __name__ == '__main__':
    main()
