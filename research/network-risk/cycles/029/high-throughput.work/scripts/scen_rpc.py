"""Cycle 29 high-throughput, leads L-1178: the 23 multi-transaction scenarios of
cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py, run transaction by transaction through eth_call.
State is carried between transactions by full-account state overrides ('state', which replaces all storage) built from
the reference interpreter's world after the previous transaction, so each eth_call starts from exactly the reference
prestate. The PoolManager is this checkout's build at 0x188d...ea8e (the real Monad PoolManager address; on MegaETH an
empty address). Every output is compared byte for byte with tools/opdiff/pyevm.py. Read-only, no transactions.
Usage: python3 -I scen_rpc.py <out.json> <url> [gas]"""
import sys, os, json, hashlib, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import scen28 as S
from evm import rpc

def main():
    out, url = sys.argv[1], sys.argv[2]
    gas = int(sys.argv[3]) if len(sys.argv) > 3 else 100_000_000
    res = {'url': url, 'gas': gas, 'clientBefore': rpc(url, 'web3_clientVersion', []), 'scenarios': {}}
    tot = eq = 0
    only = [x for x in os.environ.get('ONLY', '').split('|') if x]
    for nm, sc in S.SCEN.items():
        if only and not any(nm.startswith(x) for x in only): continue
        cs = S.codes_for(S.PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
        wd = S.P.World(cs)
        for k, v in sc['storage'].items(): wd.storage[(S.PM, int(k, 16))] = int(v, 16)
        rows = []
        for i, tx in enumerate(sc['txs']):
            # prestate override from the reference world
            ov = {}
            for a, code in wd.codes.items():
                st = {'0x%064x' % s: '0x%064x' % v for (aa, s), v in wd.storage.items() if aa == a and v}
                ov['0x%040x' % a] = {'code': '0x' + code.hex(), 'state': st}
            for a, b in wd.balances.items():
                ov.setdefault('0x%040x' % a, {})['balance'] = hex(b)
            wd.transient = {}
            ok, ret = wd.call(S.EOA, S.addr(tx['to']), 0, bytes.fromhex(tx['data']), False, 0)
            call = {'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.addr(tx['to']), 'data': '0x' + tx['data'], 'gas': hex(gas)}
            r = None; err = None
            for k in range(4):
                try:
                    blk = rpc(url, 'eth_blockNumber', [])
                    r = rpc(url, 'eth_call', [call, blk, ov], timeout=120); err = None; break
                except Exception as e:  # noqa
                    err = str(e)[:400]; time.sleep(3 * (k + 1))
            row = {'tx': i, 'kind': tx['kind'], 'refOk': ok, 'refHash': hashlib.sha256(ret).hexdigest(), 'block': blk}
            if r is not None:
                got = bytes.fromhex(r[2:])
                row['equal'] = ok and got == ret
                if not row['equal']: row['got'] = r[:3000]; row['ref'] = ret.hex()[:3000]
            else:
                # a revert comes back as an error carrying the revert data
                row['error'] = err
                row['equal'] = (not ok) and 'revert' in (err or '') and (ret.hex() in (err or '') or (len(ret) == 0))
                if not row['equal']: row['ref'] = ret.hex()[:3000]
            tot += 1; eq += bool(row['equal'])
            rows.append(row)
        res['scenarios'][nm] = rows
        print(nm, 'txs', len(rows), 'equal', sum(1 for x in rows if x['equal']), flush=True)
    res['clientAfter'] = rpc(url, 'web3_clientVersion', [])
    res['total'] = tot; res['equal'] = eq
    print('total', tot, 'equal', eq, res['clientBefore'], res['clientAfter'])
    json.dump(res, open(out, 'w'), indent=1)

if __name__ == '__main__': main()
