"""Cycle 29 op-stack-eth, lead L-1177 part 2: the 23 multi-transaction scenarios of
cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py, run read-only through eth_simulateV1 on a public
endpoint and compared byte for byte with the pyevm reference that scen28.ref() computes.

Each transaction of a scenario is one call in its own simulated block, so persistent storage carries from one
transaction to the next and transient storage starts empty in each, which is what scen28.ref() models. The first
simulated block carries the state overrides: the build of this checkout at scen28.PM, the cycle 25 driver at D and S,
the token double and forwarders (common.codes_for), the scenario's extra codes and its PoolManager storage. Nothing is
sent. Every scenario is bracketed by web3_clientVersion.
Usage: python3 scen_rpc.py <out.json> <url> [names...]"""
import sys, os, json, time, hashlib
S28 = '/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts'
sys.path.insert(0, S28)
import scen28 as X  # noqa: E402
from evm import rpc  # noqa: E402

def ov_for(sc):
    cs = X.codes_for(X.PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
    ov = {'0x%040x' % a: {'code': '0x' + c.hex()} for a, c in cs.items()}
    if sc['storage']:
        ov['0x%040x' % X.PM]['stateDiff'] = {'0x%064x' % int(k, 16): '0x%064x' % int(v, 16) for k, v in sc['storage'].items()}
    return ov

def main():
    out, url = sys.argv[1], sys.argv[2]; names = sys.argv[3:] or list(X.SCEN)
    gas = int(os.environ.get('GAS', '25000000'))
    res = {'url': url, 'gas': gas, 'scenarios': {}}
    for nm in names:
        sc = X.SCEN[nm]
        ref_outs, _ = X.ref(sc)
        blocks = []
        for i, tx in enumerate(sc['txs']):
            b = {'calls': [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % X.addr(tx['to']), 'data': '0x' + tx['data'], 'gas': hex(gas)}]}
            if i == 0: b['stateOverrides'] = ov_for(sc)
            blocks.append(b)
        r = {'ntx': len(sc['txs'])}
        for k in range(4):
            try:
                r['clientBefore'] = rpc(url, 'web3_clientVersion', [], 30)
                blk = rpc(url, 'eth_blockNumber', [], 30); r['block'] = int(blk, 16)
                sim = rpc(url, 'eth_simulateV1', [{'blockStateCalls': blocks, 'validation': False}, blk], 180)
                r['clientAfter'] = rpc(url, 'web3_clientVersion', [], 30)
                break
            except Exception as e:  # noqa
                r['error'] = str(e)[:400]; sim = None; time.sleep(3 * (k + 1))
        if sim is None:
            res['scenarios'][nm] = r; print(nm, 'ERROR', r['error'][:200], flush=True); continue
        r.pop('error', None)
        # eth_simulateV1 puts the revert data of a failed call in error.data and leaves returnData empty
        got = [(c['status'] == '0x1', (c['returnData'] if c['status'] == '0x1' else (c.get('error') or {}).get('data') or '0x')[2:])
               for b in sim for c in b['calls']]
        time.sleep(float(os.environ.get('PAUSE', '0')))
        diffs = []
        for i, ((rok, rret), (gok, gret)) in enumerate(zip(ref_outs, got)):
            if rok != gok: diffs.append({'tx': i, 'what': 'status', 'ref': rok, 'got': gok, 'gotRet': gret[:200]})
            elif rret != gret: diffs.append({'tx': i, 'what': 'output', 'refHash': hashlib.sha256(bytes.fromhex(rret)).hexdigest()[:16],
                                             'gotHash': hashlib.sha256(bytes.fromhex(gret)).hexdigest()[:16]})
        if len(got) != len(ref_outs): diffs.append({'what': 'tx count', 'ref': len(ref_outs), 'got': len(got)})
        r['diffs'] = diffs; r['bytesCompared'] = sum(len(x[1]) // 2 for x in ref_outs)
        r['gasUsed'] = [int(c['gasUsed'], 16) for b in sim for c in b['calls']]
        r['refFailed'] = [i for i, (ok, _) in enumerate(ref_outs) if not ok]
        res['scenarios'][nm] = r
        print(nm, r['clientBefore'], r['clientAfter'], 'txs', len(got), 'bytes', r['bytesCompared'], 'diffs', len(diffs), diffs[:2], flush=True)
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
