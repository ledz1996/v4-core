"""Sequence c2 of cycle 26 theme-stateful-interpreter (a beforeSwap hook writes slot0 in a nested frame between
PoolManager.sol:196 and the read in Pool.swap) on the Pocket Ethereum gateway, repeated until both web3_clientVersion
brackets name the wanted build, then compared word by word with that unit's reference interpreter.
Read-only: eth_call with state overrides only. Usage: python3 c2pin.py <out.json> <build substring> [max tries] [seq]"""
import sys, os, json, time
W = '/home/user/v4-core/research/network-risk/cycles/026/theme-stateful-interpreter.work'
sys.path.insert(0, os.path.join(W, 'scripts'))
import seqlib as S
import pyevm as P
from evm import rpc
URL = 'https://eth.api.pocket.network'
out, want = sys.argv[1], sys.argv[2]; tries = int(sys.argv[3]) if len(sys.argv) > 3 else 60
name = sys.argv[4] if len(sys.argv) > 4 else 'c2'
salt = json.load(open(os.path.join(W, 'build', 'salt.json')))['salt']
st = S.sequences(salt)[name]
PM = 0x000000000004444c5dc75cB358380D2e3dE08A90
wd = P.World(S.codes(PM)); ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(st), False, 0)
ref = S.dec_run(ret) if ok else {'topFail': ret.hex()}
def cv():
    try: return rpc(URL, 'web3_clientVersion', [], timeout=30)
    except Exception as e: return 'error ' + str(e)[:80]
runs = []
for t in range(tries):
    b = cv()
    if want not in b: runs.append({'clientBefore': b, 'skipped': True}); continue
    try:
        blk = rpc(URL, 'eth_blockNumber', [], timeout=30)
        r = rpc(URL, 'eth_call', [{'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.D, 'data': '0x' + S.enc_run(st).hex(), 'gas': hex(50_000_000)}, blk, S.overrides(PM)], timeout=180)
        got = S.dec_run(bytes.fromhex(r[2:])); err = None
    except Exception as e:
        got = None; err = str(e)[:300]; blk = None
    a = cv()
    rec = {'clientBefore': b, 'clientAfter': a, 'block': blk, 'error': err}
    if got is not None:
        rec['match'] = (got == ref); rec['words'] = sum(len(s.get('w', [])) for s in got)
        if not rec['match']: rec['got'] = got
    runs.append(rec); print(t, b[:30], a[:30], rec.get('match'), err, flush=True)
    if b == a and want in a and rec.get('match') is not None:
        if sum(1 for x in runs if x.get('clientBefore') == x.get('clientAfter') and want in x.get('clientAfter', '') and x.get('match') is not None) >= 3: break
    time.sleep(1)
pinned = [x for x in runs if x.get('clientBefore') == x.get('clientAfter') and want in (x.get('clientAfter') or '') and x.get('match') is not None]
json.dump({'seq': name, 'nsteps': len(st), 'build': want, 'refWords': sum(len(s.get('w', [])) for s in ref) if isinstance(ref, list) else None,
           'pinnedRuns': len(pinned), 'pinnedMatches': sum(1 for x in pinned if x['match']), 'runs': runs}, open(out, 'w'), indent=1)
print('pinned', len(pinned), 'matches', sum(1 for x in pinned if x['match']))
