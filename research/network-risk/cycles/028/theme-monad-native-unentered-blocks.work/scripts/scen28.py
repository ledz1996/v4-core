"""Cycle 28: multi-transaction scenarios that enter PoolManager blocks no earlier harness case entered in native code.
Each scenario is a list of transactions with state carried between them: EOA -> driver run(bytes[]) (cycle 25 driver,
kind 7 raw PoolManager calls inside unlock), EOA -> driver outside(bytes[]) (calls made while locked, full return data
kept), and EOA -> PoolManager directly. Every scenario runs in Monad's interpreter and native code (build/<ver>/hxfcov,
coverage on) and in tools/opdiff/pyevm.py, and the three are compared word for word.
Deterministic, no random sampling. Usage: python3 -I scen28.py <outdir> [names...]"""
import sys, os, json, re, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
S25 = os.path.abspath(os.path.join(W, '..', '..', '025', 'theme-unexecuted-sides.work', 'scripts'))
sys.path.insert(0, S25)
from common import *  # noqa
import v4math as V
import pyevm as P
PM = 0x188d586ddcf52439676ca21a244753fa19f9ea8e
hb = json.load(open(os.path.join(WORK, 'build', 'driver-hx.json')))
DRV_HX = bytes.fromhex(hb['driver']).replace(PLACEHOLDER, PM.to_bytes(20, 'big'))
I127 = (1 << 127) - 1
CUR_SLOT = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
RES_SLOT = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
LOCK_SLOT = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
OTHER = 0x00000000000000000000000000000000000b0b0b
SCEN = {}
_k = [0]

def key(fee=500, ts=60, hooks=0):
    i = _k[0]; _k[0] += 1
    t0 = 0x0000000000000000000000000000000020280000 + 2 * i
    return dict(kind=7, t0=t0, t1=t0 + 1, fee=fee, ts=ts, hooks=hooks)

def run_tx(c, calls, settle=True, mint0=0, mint1=0, cid=0):
    cc = dict(c, id=cid, p=raw_p(mint0, mint1, settle, calls))
    return {'to': 'D', 'kind': 'run', 'data': enc_run([cc]).hex()}

def out_tx(calls):
    return {'to': 'D', 'kind': 'outside', 'data': enc_bytes_array(SEL_OUTSIDE, calls).hex()}

def pm_tx(data):
    return {'to': 'PM', 'kind': 'pm', 'data': data.hex()}

def add(name, c, txs, storage=None, note='', codes=None):
    SCEN[name] = {'key': c, 'txs': txs, 'storage': {hex(k): hex(v) for k, v in (storage or {}).items()}, 'note': note,
                  'codes': {hex(a): b.hex() for a, b in (codes or {}).items()}}

def tick_slot(c, t): return int.from_bytes(keccak(w(t) + w(pool_slot(c) + 4)), 'big')
def acc_slot(cur): return int.from_bytes(keccak(w(cur) + w(1)), 'big')
def sel4(sig): return keccak(sig.encode())[:4]
def ext_arr(slots): return sel('extsload(bytes32[])') + w(0x20) + w(len(slots)) + b''.join(w(s) for s in slots)
def ext_n(start, n): return sel('extsload(bytes32,uint256)') + w(start) + w(n)
def ttl_arr(slots): return sel('exttload(bytes32[])') + w(0x20) + w(len(slots)) + b''.join(w(s) for s in slots)
def tick_reads(c, ticks):
    out = []
    for t in ticks: out.append(ext_n(tick_slot(c, t), 3))
    return out
def setpf(c, f): return pm_call(f'setProtocolFee({KEY},uint24)', key_words(c) + [f])
def collect(to, cur, a): return pm_call('collectProtocolFees(address,address,uint256)', [to, cur, a])

# ---- A. clearTick on liquidity removal (Pool.sol:195-202), never entered in native code before ----
c = key(); P96 = 1 << 96
add('A1 remove all, both ticks flip', c, [run_tx(c, [c_init(c, P96), c_mlp(c, -120, 120, 10 ** 18), c_mlp(c, -120, 120, -10 ** 18)]),
    out_tx(tick_reads(c, (-120, 120)) + [ext_n(pool_slot(c), 4)])])
c = key()
add('A2 shared lower tick, only upper flips', c, [run_tx(c, [c_init(c, P96), c_mlp(c, -120, 120, 10 ** 18), c_mlp(c, -120, 240, 3 * 10 ** 17),
    c_mlp(c, -120, 120, -10 ** 18)]), out_tx(tick_reads(c, (-120, 120, 240)))])
c = key()
add('A3 shared upper tick, only lower flips', c, [run_tx(c, [c_init(c, P96), c_mlp(c, -120, 120, 10 ** 18), c_mlp(c, -240, 120, 3 * 10 ** 17),
    c_mlp(c, -120, 120, -10 ** 18)]), out_tx(tick_reads(c, (-240, -120, 120)))])
c = key(fee=3000)
add('A4 swaps across both ticks, remove all, re-add, swap, poke', c, [
    run_tx(c, [c_init(c, P96), c_mlp(c, -600, 600, 10 ** 20), c_mlp(c, -120, 120, 10 ** 19),
               c_swap(c, True, -10 ** 18, V.get_sqrt_price_at_tick(-300)), c_swap(c, False, -2 * 10 ** 18, V.get_sqrt_price_at_tick(300)),
               c_swap(c, True, -10 ** 18, P96)]),
    out_tx(tick_reads(c, (-600, -120, 120, 600))),
    run_tx(c, [c_mlp(c, -120, 120, -10 ** 19)]),
    out_tx(tick_reads(c, (-600, -120, 120, 600)) + [ext_n(pool_slot(c), 4)]),
    run_tx(c, [c_mlp(c, -120, 120, 7 * 10 ** 18), c_swap(c, True, -5 * 10 ** 17, V.get_sqrt_price_at_tick(-200)), c_mlp(c, -120, 120, 0),
               c_mlp(c, -120, 120, -7 * 10 ** 18)]),
    out_tx(tick_reads(c, (-600, -120, 120, 600)) + [ext_n(pool_slot(c), 4)])])
c = key(fee=500, ts=60)
lo, hi = -887220, 887220
add('A5 full range and negative ticks, remove all', c, [run_tx(c, [c_init(c, V.get_sqrt_price_at_tick(-700000)), c_mlp(c, lo, -600000, 10 ** 15),
    c_mlp(c, lo, hi, 10 ** 12), c_swap(c, False, -10 ** 9, V.get_sqrt_price_at_tick(-650000)), c_mlp(c, lo, -600000, -10 ** 15),
    c_mlp(c, lo, hi, -10 ** 12)]), out_tx(tick_reads(c, (lo, -600000, hi)) + [ext_n(pool_slot(c), 4)])])
c = key(fee=0, ts=1)
add('A6 tick spacing 1, adjacent ticks, partial then full removal', c, [run_tx(c, [c_init(c, P96), c_mlp(c, -1, 0, 5 * 10 ** 18),
    c_mlp(c, 0, 1, 5 * 10 ** 18), c_swap(c, True, -10 ** 15, V.get_sqrt_price_at_tick(-1)), c_mlp(c, -1, 0, -10 ** 18), c_mlp(c, -1, 0, -4 * 10 ** 18),
    c_mlp(c, 0, 1, -5 * 10 ** 18)]), out_tx(tick_reads(c, (-1, 0, 1)) + [ext_n(pool_slot(c), 4)])])

# ---- B. read functions an ordinary account can call: extsload/exttload arrays, supportsInterface, getters ----
c = key()
setup = run_tx(c, [c_init(c, P96), c_mlp(c, -120, 120, 10 ** 18), c_swap(c, True, -10 ** 15, V.get_sqrt_price_at_tick(-60))])
ps = pool_slot(c)
B_calls = [ext_arr([]), ext_arr([ps]), ext_arr([ps, ps + 1, ps + 2, ps + 3]), ext_arr([tick_slot(c, -120) + i for i in range(3)] + [0, 1, 2, 3, 6, M]),
           ext_arr([ps + (i * 7919) % 5 for i in range(40)]),
           ext_n(ps, 0), ext_n(ps, 1), ext_n(ps, 4), ext_n(tick_slot(c, 120), 3), ext_n(M, 2), ext_n(ps, 64),
           ext_n(ps, 1 << 251), ext_n(ps, (1 << 251) + 3), ext_n(ps, (1 << 256) - 1),
           ttl_arr([]), ttl_arr([CUR_SLOT, RES_SLOT, LOCK_SLOT]), ttl_arr([i for i in range(9)])]
add('B1 extsload and exttload arrays from an EOA', c, [setup] + [pm_tx(x) for x in B_calls])
c2 = key()
add('B2 sync then exttload of the synced slots in one locked transaction', c2, [
    run_tx(c2, [c_init(c2, P96), c_mlp(c2, -120, 120, 10 ** 18)]),
    out_tx([c_simple('sync(address)', c2['t0']), ttl_arr([CUR_SLOT, RES_SLOT, LOCK_SLOT, 5]), ext_arr([pool_slot(c2) + 3]),
            c_simple('sync(address)', 0), ttl_arr([CUR_SLOT, RES_SLOT]), c_simple('sync(address)', c2['t1']), ttl_arr([RES_SLOT, CUR_SLOT]),
            c_simple('settle()'), c_simple('take(address,address,uint256)', c2['t0'], OTHER, 0), c_simple('clear(address,uint256)', c2['t0'], 0),
            c_simple('settleFor(address)', OTHER), c_simple('mint(address,uint256,uint256)', OTHER, 1, 0), c_simple('burn(address,uint256,uint256)', OTHER, 1, 0),
            c_simple('updateDynamicLPFee((address,address,uint24,int24,address),uint24)', *key_words(c2), 0),
            pm_call(f'initialize({KEY},uint160)', key_words(dict(c2, fee=3000)) + [P96]),
            c_mlp(c2, -120, 120, 1), c_swap(c2, True, -1, MIN_SQRT + 1), c_donate(c2, 0, 0)])])
iface = [bytes.fromhex(x) for x in ('01ffc9a7', '0f632fb3', 'ffffffff', '00000000', '80ac58cd', 'd9b67a26')]
def si(b4, dirty=0): return sel('supportsInterface(bytes4)') + (int.from_bytes(b4, 'big') << 224 | dirty).to_bytes(32, 'big')
c3 = key()
add('B3 supportsInterface, owner, controller, accrued fees, malformed array calldata', c3, [pm_tx(si(b)) for b in iface] + [
    pm_tx(si(iface[0], 1)), pm_tx(c_simple('owner()')), pm_tx(c_simple('protocolFeeController()')),
    pm_tx(c_simple('protocolFeesAccrued(address)', c3['t0'])), pm_tx(c_simple('protocolFeesAccrued(address)', 0)),
    pm_tx(sel('extsload(bytes32[])') + w(0x20)), pm_tx(sel('extsload(bytes32[])') + w(1 << 64) + w(1)),
    pm_tx(sel('extsload(bytes32[])') + w(0x20) + w(1 << 64)), pm_tx(sel('extsload(bytes32[])') + w(0x20) + w(3) + w(1)),
    pm_tx(sel('exttload(bytes32[])') + w(0x40) + w(0) + w(2) + w(7) + w(8)), pm_tx(sel('extsload(bytes32,uint256)') + w(1)),
    pm_tx(sel('exttload(bytes32[])')), pm_tx(sel('extsload(bytes32[])') + w(0x20) + w((1 << 64) - 1))],
    storage={0: OTHER, 2: OTHER + 1, acc_slot(c3['t0']): 12345})

# ---- C. owner and fee controller paths (governance actor), set by storage override ----
c = key(fee=3000)
pf = 1000 | (1000 << 12)
add('C1 owner and controller are the driver: set fee, accrue, collect, transfer ownership', c, [
    run_tx(c, [c_init(c, P96), c_mlp(c, -600, 600, 10 ** 20)]),
    out_tx([c_simple('setProtocolFeeController(address)', D), setpf(c, pf), setpf(c, 1001), setpf(c, 1001 << 12),
            setpf(dict(c, fee=500), pf), c_simple('protocolFeeController()')]),
    run_tx(c, [c_swap(c, True, -10 ** 18, V.get_sqrt_price_at_tick(-300)), c_swap(c, False, 3 * 10 ** 17, V.get_sqrt_price_at_tick(300)),
               c_swap(c, False, -10 ** 18, V.get_sqrt_price_at_tick(300))]),
    out_tx([c_simple('protocolFeesAccrued(address)', c['t0']), c_simple('protocolFeesAccrued(address)', c['t1']),
            collect(OTHER, c['t0'], 0), collect(OTHER, c['t1'], 1), collect(OTHER, c['t1'], M), c_simple('sync(address)', c['t1']),
            collect(OTHER, c['t1'], 0), c_simple('sync(address)', 0), collect(OTHER, c['t1'], 0), collect(OTHER, 0, 0),
            c_simple('protocolFeesAccrued(address)', c['t1']), setpf(c, 0), c_simple('transferOwnership(address)', S),
            c_simple('setProtocolFeeController(address)', D), c_simple('owner()'), c_simple('transferOwnership(address)', D)]),
    run_tx(c, [c_swap(c, True, -10 ** 17, V.get_sqrt_price_at_tick(-300))])],
    storage={0: D}, note='actor governance: the owner and controller are set by storage override')
c = key()
add('C2 driver is neither owner nor controller', c, [run_tx(c, [c_init(c, P96)]),
    out_tx([setpf(c, 1), collect(OTHER, c['t0'], 0), c_simple('setProtocolFeeController(address)', D), c_simple('transferOwnership(address)', D)])],
    storage={0: OTHER, 2: OTHER})
# ---- D. Position.sol:94-96 512-bit Q128 mulDiv with observable result (fees owed), more operands than case 1510 ----
for nd, amt, L in [(3, I127, 2), (4, I127, 3), (2, I127, 5), (5, (1 << 126) + 12345, 2), (3, I127, 1), (6, I127, 7)]:
    c = key(fee=500)
    add(f'D donations {nd} x {amt:#x} to L={L}, poke, collect', c, [run_tx(c, [c_init(c, P96), c_mlp(c, -60, 60, L)] + [c_donate(c, amt, amt // 3)] * nd
        + [c_mlp(c, -60, 60, 0)]), run_tx(c, [c_mlp(c, -60, 60, -L)])])

# ---- E. reverts reachable by any account: short calldata, unknown selector, a DELEGATECALL into the PoolManager ----
XDC = 0x0000000000000000000000000000000000de1e9a
DCF = assemble(['CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', PM), 'GAS', 'DELEGATECALL',
                'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'ok'), 'JUMPI',
                'RETURNDATASIZE', ('PUSH', 0), 'REVERT', ('LABEL', 'ok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN'])
c = key()
def dc_tx(data): return {'to': 'XDC', 'kind': 'pm', 'data': data.hex()}
add('E1 short calldata, unknown selector, delegatecall into the PoolManager', c, [
    pm_tx(b''), pm_tx(b'\x01\x02\x03'), pm_tx(bytes.fromhex('deadbeef') + w(1)),
    dc_tx(c_init(c, P96)), dc_tx(c_mlp(c, -60, 60, 1)), dc_tx(c_swap(c, True, -1, MIN_SQRT + 1)), dc_tx(c_donate(c, 1, 1)),
    dc_tx(c_simple('extsload(bytes32)', 0)), dc_tx(ext_n(0, 2)), dc_tx(pm_call('modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)', key_words(c) + [-60, 60, 1, 0], False) + w(0x120) + w(1 << 64))],
    codes={XDC: DCF})

# ---- F. single swaps, one per run transaction, for the exact-fraction check (pool snapshot before and after each) ----
FSW = [(True, -10 ** 18), (False, 3 * 10 ** 17), (False, -2 * 10 ** 18), (True, 5 * 10 ** 17), (True, -1), (False, -2), (True, 1), (False, 7)]
for pfv, lp in [(0, 3000), (1000 | (1000 << 12), 3000), (1 | (999 << 12), 500), (0, 0), (1000 | (1000 << 12), 0)]:
    c = key(fee=lp)
    txs = [run_tx(c, [c_init(c, P96), c_mlp(c, -600, 600, 10 ** 20)])]
    if pfv: txs.append(out_tx([setpf(c, pfv)]))
    for zfo, amt in FSW:
        txs.append(run_tx(c, [c_swap(c, zfo, amt, V.get_sqrt_price_at_tick(-590) if zfo else V.get_sqrt_price_at_tick(590))]))
    txs.append(out_tx([c_simple('protocolFeesAccrued(address)', c['t0']), c_simple('protocolFeesAccrued(address)', c['t1'])]))
    add(f'F swaps lp={lp} pf={pfv:#x}', c, txs, storage={0: D, 2: D}, note='exact-fraction check of every swap')

def world_hx(sc):
    c = sc['key']; lines = [f'code {PM:040x} {pm_build(PM).hex()}', f'code {D:040x} {DRV_HX.hex()}', f'code {S:040x} {DRV_HX.hex()}']
    for t in (c['t0'], c['t1']): lines += [f'token {t:040x}', f'tok {t:040x} {D:040x} {(1 << 250):x}']
    for k, v in sc['storage'].items(): lines.append(f'st {PM:040x} {int(k, 16):064x} {int(v, 16):064x}')
    for a, b in sc.get('codes', {}).items(): lines.append(f'code {int(a, 16):040x} {b}')
    return '\n'.join(lines) + '\n'

def addr(t): return {'D': D, 'PM': PM, 'XDC': XDC}[t]

def ref(sc):
    cs = codes_for(PM, [sc['key']]); cs.update({int(a, 16): bytes.fromhex(b) for a, b in sc.get('codes', {}).items()})
    wd = P.World(cs)
    for k, v in sc['storage'].items(): wd.storage[(PM, int(k, 16))] = int(v, 16)
    outs = []
    for tx in sc['txs']:
        wd.transient = {}
        ok, ret = wd.call(EOA, addr(tx['to']), 0, bytes.fromhex(tx['data']), False, 0)
        outs.append((ok, ret.hex()))
    return outs, {hex(k[1]): hex(v) for k, v in wd.storage.items() if k[0] == PM and v}

def parse_dump(d):
    txs = re.findall(r'tx (\d+) status=(\w+) gasleft=(\d+) out=([0-9a-f]*)', d)
    st = {}
    for m in re.finditer(r'  st ([0-9a-f]+) ([0-9a-f]+) ([0-9a-f]+)', d):
        if int(m.group(1), 16) == PM and int(m.group(3), 16): st[hex(int(m.group(2), 16))] = hex(int(m.group(3), 16))
    return [(s, int(g), o) for _, s, g, o in txs], st

def decode(tx, ok, out):
    b = bytes.fromhex(out)
    if not ok: return {'revert': out}
    if tx['kind'] == 'run':
        r = dec_run(b)[0]
        return {'ok': r[0], 'w': [hex(x) for x in r[1]] if r[1] else None, 'revert': r[2].hex()}
    if tx['kind'] == 'outside': return {'calls': dec_outside(b)}
    return {'out': out}

def compare(sc, ref_outs, ref_st, eng_txs, eng_st):
    diffs = []
    for i, (tx, (rok, rret), (es, eg, eo)) in enumerate(zip(sc['txs'], ref_outs, eng_txs)):
        eok = es == 'success'
        if rok != eok: diffs.append(f'tx {i} status ref={rok} engine={es}'); continue
        if tx['kind'] == 'run' and rok:
            a = decode(tx, 1, rret); b = decode(tx, 1, eo)
            if a['ok'] != b['ok'] or a['revert'] != b['revert']: diffs.append(f'tx {i} run status'); continue
            if a['w'] and b['w']:
                # the last two words are the driver's own token balances, which differ by design (the pyevm driver mints,
                # the harness driver is pre-funded with 2^250 and transfers)
                if a['w'][:-2] != b['w'][:-2]: diffs.append(f'tx {i} run words')
        elif rret != eo: diffs.append(f'tx {i} output')
    if len(ref_outs) != len(eng_txs): diffs.append('tx count')
    if ref_st != eng_st:
        ks = sorted(set(ref_st) | set(eng_st)); diffs.append('PM storage: ' + ', '.join(f'{k} ref={ref_st.get(k)} eng={eng_st.get(k)}' for k in ks if ref_st.get(k) != eng_st.get(k))[:2000])
    return diffs

def main():
    outdir = sys.argv[1]; names = sys.argv[2:] or list(SCEN)
    os.makedirs(os.path.join(outdir, 'raw'), exist_ok=True); os.makedirs(os.path.join(outdir, 'cov'), exist_ok=True)
    res = {}
    for i, nm in enumerate(names):
        sc = SCEN[nm]; tag = f's{i:02d}'
        wf = os.path.join(outdir, f'{tag}-world.txt'); open(wf, 'w').write(world_hx(sc))
        sf = os.path.join(outdir, f'{tag}-scen.txt')
        open(sf, 'w').write(f'SCEN {tag}\n' + ''.join(f'TX {EOA:040x} {addr(t["to"]):040x} 00 150000000 {t["data"]}\n' for t in sc['txs']))
        ref_outs, ref_st = ref(sc)
        r = {'name': nm, 'note': sc['note'], 'ntx': len(sc['txs']), 'ref': [{'ok': ok, **decode(t, ok, o)} for t, (ok, o) in zip(sc['txs'], ref_outs)]}
        for ver in ('0.16.5', '0.16.7'):
            env = dict(os.environ, HX_COVOUT=os.path.join(outdir, 'cov', f'{ver}-{tag}.cov'))
            p = subprocess.run([os.path.join(W, 'build', ver, 'hxfcov'), wf, sf, '-v'], capture_output=True, text=True, env=env)
            open(os.path.join(outdir, 'raw', f'{ver}-{tag}.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
            same = p.stdout.startswith('SAME')
            m = re.search(r'--- interp\n(.*)--- native\n(.*?)scenarios=', p.stdout, re.S)
            ti, si_ = parse_dump(m.group(1)); tn, sn = parse_dump(m.group(2))
            r[ver] = {'engineSame': same, 'rc': p.returncode, 'interpVsRef': compare(sc, ref_outs, ref_st, ti, si_),
                      'nativeVsRef': compare(sc, ref_outs, ref_st, tn, sn),
                      'native': [{'status': s, 'gasleft': g, **decode(t, s == 'success', o)} for t, (s, g, o) in zip(sc['txs'], tn)],
                      'gasInterp': [g for _, g, _ in ti], 'gasNative': [g for _, g, _ in tn]}
        res[nm] = r
        print(nm, {v: (r[v]['engineSame'], r[v]['interpVsRef'][:2], r[v]['nativeVsRef'][:2]) for v in ('0.16.5', '0.16.7')}, flush=True)
    json.dump({'pm': hex(PM), 'scenarios': {k: {'txs': SCEN[k]['txs'], 'storage': SCEN[k]['storage'], 'key': SCEN[k]['key']} for k in names},
               'results': res}, open(os.path.join(outdir, 'results.json'), 'w'), indent=0)

if __name__ == '__main__':
    main()
