"""Cycle 37 theme-native-face-inflows, Task 3. Read-only. Reuses the cycle 35 driver (credtab.py): a contract placed
by state override at DRV calls unlock on the deployed PoolManager, runs a script of CALL/BAL/CREATE steps in
unlockCallback and reverts with the record, so nothing persists. Cases on the five face networks:
 N1 value call to the PoolManager with empty calldata and with an unknown selector (does it accept native value),
 N2 native take naming the PoolManager as recipient,
 N3 face take naming the PoolManager as recipient between sync(face) and settle,
 N4 settleFor(X) with value after sync(0) (a relay that calls the PoolManager with value) and after sync(face),
 plus per network: Celo transfer precompile 0xfd called directly (both directions) and CELO.transfer / transferFrom
 to the PoolManager; Polygon 0x1010.transfer(PM,x) with and without value; Arc native value call, face transfers of
 1 unit and 0, a forced inflow of 1 wei and of r wei (below one face unit), and the Native Coin Authority 0x1800..00
 called directly. eth_simulateV1 (where served): two transactions in one block, sync(face) then exttload of the
 synced-currency transient slot; and an OP deposit-typed call. No randomness, no seed.
usage: python3 -I inflows.py <out.json> [chainId ...]"""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/035/theme-sync-settle-credit-table.work/scripts')
import credtab as C
from rpcu import rpc, version
ZERO, DRV = C.ZERO, C.DRV
X = '0x00000000000000000000000000000000000b0b00'
CUR = '0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9'
RES = '0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95'
FACE = {42220: '0x471ece3750da237f93b8e339c536989b8978a438', 137: '0x0000000000000000000000000000000000001010',
        5042: '0x3600000000000000000000000000000000000000', 10: '0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000',
        7777777: '0xdeaddeaddeaddeaddeaddeaddeaddeaddead0000'}
URL = {42220: 'https://forno.celo.org', 137: 'https://polygon-bor-rpc.publicnode.com', 5042: 'https://rpc.mainnet.arc.io',
       10: 'https://mainnet.optimism.io', 7777777: 'https://rpc.zora.energy/'}
PM = {42220: '0x288dc841a52fca2707c6947b3a777c5e56cd87bc', 137: '0x67366782805870060151383f4bbff9dab53e5cd6',
      5042: '0x8366a39cc670b4001a1121b8f6a443a643e40951', 10: '0x9a13f98cb987694c9f086b1f5eb990eea8264ec3',
      7777777: '0x0575338e4c17006ae181b47900a84404247ca30f'}
S = C.sel
def sync(pm, c, l): return C.CALL(pm, S('sync(address)') + C.a32(c), label=l)
def settle(pm, l='settle() value 0', v=0): return C.CALL(pm, S('settle()'), value=v, label=l)
def delta(pm, who, c, l): return C.CALL(pm, S('exttload(bytes32)') + C.dslot(who, c), label=l)
def tl(pm, slot, l): return C.CALL(pm, S('exttload(bytes32)') + bytes.fromhex(slot[2:]), label=l)
def bof(f, who, l): return C.CALL(f, C.balOf(f, who), label=l)
def force(pm, v, l): return C.CREATE(v, bytes([0x73]) + bytes.fromhex(pm[2:]) + bytes([0xff]), l)

def common(cid, pm, f, x):
    cs = {}
    cs['N1 value call to PM'] = [C.BAL(pm, 'PM native before'), C.CALL(pm, b'', value=x, label='CALL PM value x, empty calldata'),
        C.CALL(pm, bytes.fromhex('deadbeef'), value=x, label='CALL PM value x, unknown selector'), C.BAL(pm, 'PM native after')]
    cs['N2 native take to PM'] = [C.BAL(pm, 'PM native before'), C.CALL(pm, S('take(address,address,uint256)') + C.a32(ZERO) + C.a32(pm) + C.w(x), label='take(native, PM, x)'),
        C.BAL(pm, 'PM native after'), delta(pm, DRV, ZERO, 'delta(driver,native)')]
    cs['N3 face take to PM inside sync'] = [bof(f, pm, 'face balanceOf(PM) before'), sync(pm, f, 'sync(face)'),
        C.CALL(pm, S('take(address,address,uint256)') + C.a32(f) + C.a32(pm) + C.w(x), label='take(face, PM, x)'),
        bof(f, pm, 'face balanceOf(PM) after take'), settle(pm), delta(pm, DRV, f, 'delta(driver,face)')]
    cs['N4 relay-style settleFor with value'] = [sync(pm, ZERO, 'sync(0)'), C.CALL(pm, S('settleFor(address)') + C.a32(X), value=x, label='settleFor(X) value x after sync(0)'),
        delta(pm, X, ZERO, 'delta(X,native)'), delta(pm, DRV, ZERO, 'delta(driver,native)'),
        sync(pm, f, 'sync(face)'), C.CALL(pm, S('settleFor(address)') + C.a32(X), value=x, label='settleFor(X) value x after sync(face)'),
        tl(pm, CUR, 'synced currency slot after'), delta(pm, X, f, 'delta(X,face)')]
    return cs

def specific(cid, pm, f, x, pmbal):
    cs = {}
    if cid == 42220:
        P = '0x00000000000000000000000000000000000000fd'
        cs['Celo transfer precompile direct'] = [C.BAL(pm, 'PM native before'),
            C.CALL(P, C.a32(pm) + C.a32(DRV) + C.w(x), label='0xfd(from=PM,to=driver,x) from driver'),
            C.CALL(P, C.a32(DRV) + C.a32(pm) + C.w(x), label='0xfd(from=driver,to=PM,x) from driver'),
            C.BAL(pm, 'PM native after'), C.BAL(DRV, 'driver native after')]
        cs['Celo CELO.transfer to PM between sync and settle'] = [bof(f, pm, 'face before'), C.BAL(pm, 'PM native before'), sync(pm, f, 'sync(CELO)'),
            C.CALL(f, S('transfer(address,uint256)') + C.a32(pm) + C.w(x), label='driver CELO.transfer(PM,x)'),
            C.CALL(f, S('transferFrom(address,address,uint256)') + C.a32(X) + C.a32(pm) + C.w(1), label='CELO.transferFrom(X,PM,1) no allowance'),
            bof(f, pm, 'face after'), C.BAL(pm, 'PM native after'), settle(pm), delta(pm, DRV, f, 'delta(driver,CELO)')]
    if cid == 137:
        cs['Polygon 0x1010.transfer to PM between sync and settle'] = [bof(f, pm, 'face before'), sync(pm, f, 'sync(0x1010)'),
            C.CALL(f, S('transfer(address,uint256)') + C.a32(pm) + C.w(x), value=x, label='0x1010.transfer(PM,x) value x'),
            C.CALL(f, S('transfer(address,uint256)') + C.a32(pm) + C.w(x), value=0, label='0x1010.transfer(PM,x) value 0'),
            bof(f, pm, 'face after'), settle(pm), delta(pm, DRV, f, 'delta(driver,0x1010)')]
    if cid == 5042:
        r = pmbal % 10**12
        cs['Arc native and face inflows between sync and settle'] = [bof(f, pm, 'face before'), C.BAL(pm, 'PM native before'), sync(pm, f, 'sync(face)'),
            C.CALL(pm, b'', value=10**12, label='native CALL PM value 1e12'),
            C.CALL(f, S('transfer(address,uint256)') + C.a32(pm) + C.w(0), label='face.transfer(PM,0)'),
            C.CALL(f, S('transfer(address,uint256)') + C.a32(pm) + C.w(1), label='face.transfer(PM,1)'),
            bof(f, pm, 'face after 1 unit'), C.BAL(pm, 'PM native after 1 unit'),
            force(pm, 1, 'forced inflow 1 wei'), bof(f, pm, 'face after 1 wei'),
            settle(pm), delta(pm, DRV, f, 'delta(driver,face)'), delta(pm, DRV, ZERO, 'delta(driver,native)')]
        cs['Arc forced inflow below one face unit'] = [bof(f, pm, 'face before'), sync(pm, f, 'sync(face)'),
            force(pm, 10**12 - r - 1, 'forced inflow 1e12-r-1 wei (one short of next unit)'), bof(f, pm, 'face after'),
            settle(pm), delta(pm, DRV, f, 'delta(driver,face)')]
        NCA = '0x1800000000000000000000000000000000000000'
        cs['Arc Native Coin Authority direct'] = [C.BAL(pm, 'PM native before'),
            C.CALL(NCA, S('transfer(address,address,uint256)') + C.a32(pm) + C.a32(DRV) + C.w(1), label='NCA.transfer(PM,driver,1)'),
            C.CALL(NCA, S('mint(address,uint256)') + C.a32(pm) + C.w(1), label='NCA.mint(PM,1)'),
            C.CALL(NCA, S('burn(address,uint256)') + C.a32(pm) + C.w(1), label='NCA.burn(PM,1)'),
            C.BAL(pm, 'PM native after')]
    return cs

def simulate(url, pm, f, bn):
    frm = '0x00000000000000000000000000000000000a11ce'
    calls = [{'from': frm, 'to': pm, 'data': '0x' + (S('sync(address)') + C.a32(f)).hex()},
             {'from': frm, 'to': pm, 'data': '0x' + (S('exttload(bytes32)') + bytes.fromhex(CUR[2:])).hex()},
             {'from': frm, 'to': pm, 'data': '0x' + (S('exttload(bytes32)') + bytes.fromhex(RES[2:])).hex()}]
    out = {'twoTx': rpc(url, 'eth_simulateV1', [{'blockStateCalls': [{'calls': calls}]}, bn], 120)}
    # one call that does sync and exttload in the same transaction, for contrast: driver not needed, use multicall-free form
    return out

def main():
    outp = sys.argv[1]; only = set(map(int, sys.argv[2:])) or set(FACE)
    res = {}
    for cid in [42220, 137, 5042, 10, 7777777]:
        if cid not in only: continue
        url, pm, f = URL[cid], PM[cid], FACE[cid]
        r = {'url': url, 'pm': pm, 'face': f, 'before': version(url, cid), 'cases': []}
        b = rpc(url, 'eth_getBlockByNumber', ['latest', False]); bn = b['result']['number']; r['block'] = bn
        pmbal = int(rpc(url, 'eth_getBalance', [pm, bn])['result'], 16); r['pmNative'] = pmbal
        x = 10**6 if cid != 5042 else 10**13
        allc = common(cid, pm, f, x); allc.update(specific(cid, pm, f, x, pmbal))
        for name, steps in allc.items():
            rec = C.run(url, cid, pm, name, steps, bn); r['cases'].append(rec)
            print(cid, name); [print('   ', s['label'], s['ok'], s['ret'][:140]) for s in rec.get('steps', [])]
            if 'steps' not in rec: print('   RAW', str(rec['raw'])[:300])
        r['simulate'] = simulate(url, pm, f, bn); print(cid, 'simulate', str(r['simulate'])[:600])
        r['after'] = version(url, cid)
        res[cid] = r
        json.dump(res, open(outp, 'w'), indent=1)
main()
