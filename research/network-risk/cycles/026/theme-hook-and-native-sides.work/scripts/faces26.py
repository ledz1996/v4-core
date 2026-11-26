"""Native asset faces: sync of the ERC-20 face of the native asset, then settle with value, a native take, or a native
payment before the sync. Built and run on Celo (CELO token), Arc (USDC at 0x3600..), Polygon (0x1010) and, as control,
Ethereum. Usage: python3 faces26.py <outdir> <chainId> [rpc]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import *  # noqa
from evm import rpc
FACE = {42220: 0x471EcE3750Da237f93B8E339c536989b8978a438, 5042: 0x3600000000000000000000000000000000000000, 137: 0x1010, 1: 0x471EcE3750Da237f93B8E339c536989b8978a438}
NETS = {n['chainId']: n for n in json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']}
cid = int(sys.argv[2]); n = NETS[cid]; url = sys.argv[3] if len(sys.argv) > 3 else n['rpc']; pm = int(n['poolManager'], 16); f = FACE[cid]
bal = pm_call('extsload(bytes32)', [0])  # placeholder no-op read
def bof(): return bytes.fromhex('70a08231') + w(pm)
base = {'t0': 0, 't1': 0x7B0000000001, 'fee': 3000, 'ts': 60, 'hooks': 0}
acts = {
 'F1 sync(face) then settle with value 5': [(1, 0, c_sync(f)), (1, 5, c_settle())],
 'F2 sync(face), native take 5, settle()': [(1, 0, c_sync(f)), (1, 0, c_take(0, D, 5)), (1, 0, c_settle())],
 'F3 native settle 7, sync(face), settle()': [(1, 7, c_settle()), (1, 0, c_sync(f)), (1, 0, c_settle()), (1, 0, c_take(0, D, 7))],
 'F4 face balanceOf(PoolManager) and native take 10**12 then face balanceOf': [(f, 0, bof()), (1, 10 ** 12, c_settle()), (f, 0, bof()), (1, 0, c_take(0, D, 10 ** 12)), (f, 0, bof())],
}
cases = []
for k, (tag, a) in enumerate(acts.items()):
    c = dict(base); c['id'] = k; c['tag'] = tag; c['nact'] = len(a); c['p'] = build_p([], a); cases.append(c)
rec = {'chainId': cid, 'face': hex(f), 'client': rpc(url, 'web3_clientVersion', []), 'block': int(rpc(url, 'eth_blockNumber', []), 16), 'results': {}}
r = rpc(url, 'eth_call', [{'from': '0x%040x' % EOA, 'to': '0x%040x' % D, 'data': '0x' + enc_run(cases, pm).hex(), 'gas': hex(30000000)}, hex(rec['block']), overrides(pm, cases)], timeout=120)
for c, (ok, words, rv) in zip(cases, dec_run(bytes.fromhex(r[2:]))):
    d = decode_words(words, c['nact']) if words else None
    rec['results'][c['tag']] = {'unlockOk': ok, 'revert': rv.hex()[:200], 'acts': [(a['ok'], hex(a['w0'])) for a in d['acts']] if d else None,
                                'deltasDriver': [hex(x) for x in d['deltas'][:2]] if d else None, 'settleOk': d.get('settleOk') if d else None}
rec['clientAfter'] = rpc(url, 'web3_clientVersion', [])
json.dump(rec, open(os.path.join(sys.argv[1], f'faces-{cid}.json'), 'w'), indent=1)
for k, v in rec['results'].items(): print(cid, k, v['unlockOk'], v['acts'])
