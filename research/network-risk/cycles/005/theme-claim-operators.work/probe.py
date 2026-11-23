# Differential read-only probe: can an arbitrary caller make approved address X run PoolManager.transferFrom(owner, receiver, id, amount)?
# For each generic call shape the outer call is simulated twice from an unrelated account: once with amount 1 (allowed if X has the right)
# and once with amount balance+1 (always reverts in ERC6909.transferFrom). A shape is positive when the first run succeeds and the second
# reverts or returns other data. Nothing is sent; eth_call only.
import sys, json, os, concurrent.futures as cf
from lib import *
from abi2 import calldata
from state import url, bcall
ATT = '0x00000000000000000000000000000000a77ac4e5'; RCV = '0x00000000000000000000000000000000000c0ffe'
def shapes(pm, inner):
    b = bytes.fromhex(inner[2:]); S = []
    S.append(('Multicall3.aggregate', calldata('aggregate((address,bytes)[])', [[(pm, b)]])))
    S.append(('Multicall3.aggregate3', calldata('aggregate3((address,bool,bytes)[])', [[(pm, False, b)]])))
    S.append(('Multicall3.tryAggregate', calldata('tryAggregate(bool,(address,bytes)[])', [True, [(pm, b)]])))
    S.append(('Multicall3.aggregate3Value', calldata('aggregate3Value((address,bool,uint256,bytes)[])', [[(pm, False, 0, b)]])))
    S.append(('execute(address,uint256,bytes)', calldata('execute(address,uint256,bytes)', [pm, 0, b])))
    S.append(('execute(address,bytes)', calldata('execute(address,bytes)', [pm, b])))
    S.append(('executeBatch(address[],uint256[],bytes[])', calldata('executeBatch(address[],uint256[],bytes[])', [[pm], [0], [b]])))
    S.append(('executeBatch(address[],bytes[])', calldata('executeBatch(address[],bytes[])', [[pm], [b]])))
    S.append(('executeBatch((address,uint256,bytes)[])', calldata('executeBatch((address,uint256,bytes)[])', [[(pm, 0, b)]])))
    S.append(('execute((address,uint256,bytes)[])', calldata('execute((address,uint256,bytes)[])', [[(pm, 0, b)]])))
    from abi2 import enc_tuple
    ed = enc_tuple(['(address,uint256,bytes)[]'], [[(pm, 0, b)]])
    S.append(('ERC-7821 execute(bytes32,bytes) batch', calldata('execute(bytes32,bytes)', [bytes.fromhex('01' + '00' * 31), ed])))
    S.append(('ERC-7579 execute(bytes32,bytes) single', calldata('execute(bytes32,bytes)', [bytes(32), bytes.fromhex(pm[2:]) + bytes(32) + b])))
    S.append(('call(address,bytes)', calldata('call(address,bytes)', [pm, b])))
    S.append(('call(address,uint256,bytes)', calldata('call(address,uint256,bytes)', [pm, 0, b])))
    S.append(('forward(address,bytes)', calldata('forward(address,bytes)', [pm, b])))
    S.append(('exec(address,uint256,bytes)', calldata('exec(address,uint256,bytes)', [pm, 0, b])))
    S.append(('multicall((address,bytes)[])', calldata('multicall((address,bytes)[])', [[(pm, b)]])))
    S.append(('multicall(address[],bytes[])', calldata('multicall(address[],bytes[])', [[pm], [b]])))
    S.append(('functionCall(address,bytes)', calldata('functionCall(address,bytes)', [pm, b])))
    S.append(('invoke(address,uint256,bytes)', calldata('invoke(address,uint256,bytes)', [pm, 0, b])))
    S.append(('executeCall(address,uint256,bytes)', calldata('executeCall(address,uint256,bytes)', [pm, 0, b])))
    S.append(('doCall(address,bytes)', calldata('doCall(address,bytes)', [pm, b])))
    S.append(('batch((address,uint256,bytes)[])', calldata('batch((address,uint256,bytes)[])', [[(pm, 0, b)]])))
    S.append(('Safe MultiSendCallOnly.multiSend(bytes)', calldata('multiSend(bytes)', [bytes([0]) + bytes.fromhex(pm[2:]) + bytes(32) + len(b).to_bytes(32, 'big') + b])))
    S.append(('raw fallback: inner calldata sent to X', inner))
    return S
def tf(o, i, amt): return '0xfe99049a' + adr(o) + adr(RCV) + i[2:].rjust(64, '0') + u256(amt)
def probe_one(u, pm, x, o, i, bal, overrides=None):
    ok = shapes(pm, tf(o, i, 1)); bad = shapes(pm, tf(o, i, bal + 1)); res = []
    calls = []
    for (n, d) in ok + bad:
        p = [{'from': ATT, 'to': x, 'data': d}, 'latest']
        if overrides: p.append(overrides)
        calls.append(('eth_call', p))
    r = []
    for m, p in calls:
        try: r.append(('ok', rpc(u, m, p, tries=3)))
        except Exception as e: r.append(('err', str(e)[:60]))
    k = len(ok); pos = []
    for j in range(k):
        a, b_ = r[j], r[j + k]
        if a[0] == 'ok' and (b_[0] == 'err' or b_[1] != a[1]): pos.append((ok[j][0], a[1][:74], b_[1][:74]))
    return pos, sum(1 for j in range(k) if r[j][0] == 'ok')
def control():
    # positive control: Multicall3 made operator of a holder by state override on Ethereum; negative control without the override
    cid = 1; u = url(cid); pm = net(cid)['poolManager']; from keccak import keccak256
    ex = json.load(open(os.path.join(HERE, 'raw', 'exposure_1.json')))
    it = max((it for r in ex for it in r['items']), key=lambda it: it[5] or 0); o, tok, bal = it[0], it[1], int(it[4]); i = '0x' + tok[2:].rjust(64, '0')
    mc = '0xcA11bde05977b3631167028862bE2a173976CA11'
    inner = keccak256(bytes.fromhex(adr(o)) + (3).to_bytes(32, 'big')); slot = '0x' + keccak256(bytes.fromhex(adr(mc)) + inner).hex()
    print('control with override', probe_one(u, pm, mc, o, i, bal, {pm: {'stateDiff': {slot: '0x' + '1'.rjust(64, '0')}}}))
    print('control without override', probe_one(u, pm, mc, o, i, bal))
def run(cid):
    ex = json.load(open(os.path.join(HERE, 'raw', 'exposure_%d.json' % cid))); u = url(cid); pm = net(cid)['poolManager']; out = []
    def one(r):
        if not r['items'] or r['kind'] == 'EOA': return None
        st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid)))
        it = max(r['items'], key=lambda it: int(it[4])); o, tok, bal = it[0], it[1], int(it[4]); i = '0x' + tok[2:].rjust(64, '0')
        try: pos, nok = probe_one(u, pm, r['x'], o, i, bal)
        except Exception as e: return dict(x=r['x'], err=str(e)[:100])
        return dict(x=r['x'], kind=r['kind'], owner=o, id=tok, bal=str(bal), positive=pos, shapesNotReverting=nok)
    with cf.ThreadPoolExecutor(6) as exr:
        for v in exr.map(one, ex):
            if v: out.append(v)
    json.dump(out, open(os.path.join(HERE, 'raw', 'probe_%d.json' % cid), 'w'))
    return cid, 'probed', len(out), 'positive', [(v['x'], [p[0] for p in v['positive']]) for v in out if v.get('positive')], 'errs', sum(1 for v in out if v.get('err'))
if __name__ == '__main__':
    if sys.argv[1] == 'control': control(); sys.exit()
    for c in sys.argv[1:]: print(run(int(c)), flush=True)
