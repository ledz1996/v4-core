"""Cycle 17, unit theme-real-address-runs, task 1.

Runs the script sets 1, 2 and 6 of tools/opdiff (pmdiff.py, pmdiff2.py, pmdiff6.py) against the PoolManager at its
real address on one network, with the PoolManager's code, storage and balance left as they are on chain. Only the
driver (unlock callback), the token doubles and the hook doubles are placed by state override. The scripts are the
same generators with the same seeds; the only change is that every place where a script names the PoolManager
(the driver's call target, hook doubles that forward to the PoolManager, take recipients, extsload targets) names
the real address. Pools are created by the scripts with currencies and hooks at fixed doubles' addresses, so no
existing pool is touched.

mode 'real'  : the PoolManager address from state/networks.json, no override of that address
mode 'fresh' : the original fresh-address run of the tool (code placed by override, as in earlier cycles)

Usage: python3 realrun.py <set 1|2|6> <real|fresh> <chainId> <out.json.gz> [threads]
"""
import sys, os, json, gzip, hashlib, time, random, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
from evm import rpc, networks  # noqa
import pmdiff as P  # noqa

SET, MODE, CID, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
THREADS = int(sys.argv[5]) if len(sys.argv) > 5 else 4
NW = {n['chainId']: n for n in json.load(open(os.path.join(TOOLS, '..', '..', 'state', 'networks.json')))['networks']}
URL = NW[CID]['rpc']
FRESH_PM = P.PM
if MODE == 'real':
    P.PM = '0x' + NW[CID]['poolManager'][2:].lower()
# the other modules read P.PM when they are imported, so import them only now
import pmdiff2 as Q  # noqa
import pmdiff3 as R  # noqa
import pmdiff6 as S6  # noqa
PMI = int(P.PM, 16)
assert R.PMI == PMI and S6.PMI == PMI


def build():
    if SET == '1':
        rnd = random.Random(7_2026_11_24); sc = [P.script(rnd) for _ in range(250)]
        datas = [d for d, _, _ in sc]; drvaddr = P.DRV
        ov = {P.DRV: {'code': '0x' + P.driver().hex()}}
        if MODE == 'fresh':
            ov[P.PM] = {'code': '0x' + P.fetch_code().hex()}
        kinds = [k for _, k, _ in sc]
    elif SET == '2':
        rnd = random.Random(11_2026_11_24); sc = [Q.script(rnd, i) for i in range(300)]
        datas = [d for d, _, _ in sc]; drvaddr = P.DRV
        ov = {P.DRV: {'code': '0x' + Q.driver().hex()}, '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + Q.token().hex()}}
        for f in Q.HOOK_FLAGS: ov['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + Q.hook().hex()}
        if MODE == 'fresh':
            ov[P.PM] = {'code': '0x' + P.fetch_code().hex(), 'balance': hex(10 ** 19)}
        kinds = [k for _, k, _ in sc]
    else:
        SC = S6.scripts(); datas = [d for _, d in SC]; kinds = [n for n, _ in SC]
        drvaddr = '0x' + S6.DRV.to_bytes(20, 'big').hex()
        if MODE == 'fresh':
            os.environ['PM_BUILD'] = os.path.join(TOOLS, '..', '..', 'build', 'PoolManager.json')
            ov = S6.overrides(P.fetch_code())
        else:
            ov = S6.overrides(b'')
            del ov['0x' + PMI.to_bytes(20, 'big').hex()]
    return datas, kinds, drvaddr, ov


def ask(data, drv, ov, gas):
    last = None
    for k in range(6):
        try:
            return rpc(URL, 'eth_call', [{'to': drv, 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=150)
        except Exception as e:  # noqa
            last = str(e)[:300]
            if 'revert' in last.lower() and '"data"' in last: break
            if 'gas' in last.lower() and ('limit' in last.lower() or 'cap' in last.lower() or 'exceed' in last.lower()): break
            time.sleep(3 * (k + 1))
    return 'ERR ' + last


if __name__ == '__main__':
    datas, kinds, drv, ov = build()
    t0 = time.time()
    def q0(m, p):
        for k in range(8):
            try: return rpc(URL, m, p)
            except Exception as e: last = str(e); time.sleep(5 * (k + 1))  # noqa
        return 'ERR ' + last
    blk = q0('eth_blockNumber', [])
    try: ver = rpc(URL, 'web3_clientVersion', [])
    except Exception as e: ver = 'ERR ' + str(e)[:80]  # noqa
    code = q0('eth_getCode', [P.PM, 'latest']) if MODE == 'real' else ''
    with cf.ThreadPoolExecutor(THREADS) as ex:
        res = list(ex.map(lambda d: ask(d, drv, ov, 25_000_000), datas))
    out = {'set': SET, 'mode': MODE, 'chainId': CID, 'pm': P.PM, 'freshPm': FRESH_PM, 'rpc': URL, 'blockBefore': blk,
           'blockAfter': q0('eth_blockNumber', []), 'clientVersion': ver, 'pmCodeSha256': hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() if code else '',
           'pmCodeLen': (len(code) - 2) // 2 if code else 0, 'gas': 25_000_000, 'seconds': round(time.time() - t0),
           'scripts': len(datas), 'kinds': kinds, 'results': res}
    json.dump(out, gzip.open(OUT, 'wt'))
    print(SET, MODE, CID, 'done', len(res), 'errors', sum(1 for r in res if r.startswith('ERR')), 'seconds', out['seconds'])
