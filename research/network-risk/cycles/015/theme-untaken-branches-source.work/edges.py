"""Cycle 15, unit theme-untaken-branches-source.

Read-only edge runs in the style of tools/opdiff/pmdiff6.py, on the build of this checkout.

Set A (per network, no reference): the network's own special addresses named as currency (sync, the synced
words, settle, a zero take) and as hook (initialize). These are the inputs whose answer can depend on the
chain, the CALL and STATICCALL results behind the jump pairs 9042/9048 and 15088/15094 of jumpmap.json.

Set B and C (compared with the reference interpreter): hook return data of 31 to 1,048,576 bytes ahead of the
memory allocations guarded by Panic 0x41 (pcs 5583, 11761, 11789, 11817, 19089), token transfers whose return
data is 31, 32, 33 or 64 bytes, and extsload / exttload with lengths whose shl(5, n) wraps.

Usage: python3 edges.py <outdir> [A|BC] [chainId ...]
"""
import sys, os, json, hashlib, time, concurrent.futures as cf
TOOLS = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, TOOLS)
os.environ.setdefault('PM_BUILD', '/home/user/v4-core/research/network-risk/build/PoolManager.json')
from evm import rpc, networks, MASK
import pmdiff as P, pmdiff2 as Q
import pmdiff6 as M

w, it, end, key, init, swap, cfg, text, ext = M.w, M.it, M.end, M.key, M.init, M.swap, M.cfg, M.text, M.ext
PMI, DRV, T0, T1, HB, S = M.PMI, M.DRV, M.T0, M.T1, M.HB, M.S
CUR_SLOT = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
RES_SLOT = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
OTHER = 0xA11CE

# special addresses named in ASSUMPTIONS.md, OPCODES.md (cycle 13 row on callee gas) and the per network findings
SPECIAL = {
    'all': [1, 2, 3, 4, 5, 6, 7, 8, 9, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x100],
    'op': [0x4200000000000000000000000000000000000006, 0x4200000000000000000000000000000000000016,
           0x4200000000000000000000000000000000000015, 0x420000000000000000000000000000000000000F],
    42220: [0xfd, 0x471EcE3750Da237f93B8E339c536989b8978a438],
    42161: [0x64, 0x65, 0x6c, 0x6e, 0x6f, 0xc8, 0x71],
    4663: [0x64, 0x65, 0x6c, 0x6e, 0x71], 99901: [0x64, 0x65, 0x6c, 0x6e, 0x71],
    137: [0x1000, 0x1001, 0x1010], 56: [0x1000, 0x1001, 0x1002, 0x1003, 0x1004, 0x2000, 0x2002],
    43114: [0x0100000000000000000000000000000000000000, 0x0200000000000000000000000000000000000000,
            0x0200000000000000000000000000000000000005],
    143: [0x1000, 0x1001], 4326: [0x6342000000000000000000000000000000000001],
    4217: [0x20C0000000000000000000000000000000000000, 0x403C000000000000000000000000000000000000,
           0xfeEC000000000000000000000000000000000000],
    5042: [0x3600000000000000000000000000000000000000, 0x1800000000000000000000000000000000000005,
           0x1800000000000000000000000000000000000009],
    999: list(range(0x800, 0x814)) + [0x2222222222222222222222222222222222222222],
}
OPS = {10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196}


def specials(cid):
    xs = list(SPECIAL['all']) + (SPECIAL['op'] if cid in OPS else []) + SPECIAL.get(cid, [])
    return sorted(set(xs))


def valid_hook(a):
    f = a & 0x3fff
    if not f: return False
    bad = [(1 << 7, 1 << 3), (1 << 6, 1 << 2), (1 << 10, 1 << 1), (1 << 8, 1 << 0)]
    return all(not (f & d and not f & base) for base, d in bad)


def set_a(cid):
    out = []
    for x in specials(cid):
        its = [it(PMI, S['sync'] + w(x)), text(CUR_SLOT), text(RES_SLOT), it(PMI, S['settle']),
               it(PMI, S['sync'] + w(x)), it(PMI, S['take'] + w(x) + w(OTHER) + w(0)), it(PMI, S['settle'])]
        if valid_hook(x):
            its.append(it(PMI, init(key(T0, T1, 3000, 60, x), 1 << 96)))
        out.append((f'special {x:#x}', b''.join(its) + end(0)))
    return out


BEFORE_INIT = HB | (1 << 13)
AFTER_INIT = HB | (1 << 12)
BEFORE_SWAP = HB | (1 << 7)


def set_bc():
    out = []
    # B1: beforeInitialize hook answers with n bytes; callHook accepts n >= 32 with the selector (Hooks.sol:152)
    for n in (31, 32, 33, 0x1000, 0x10000, 0x40000, 0x100000):
        k = key(T0, T1, 3000, 60, BEFORE_INIT)
        out.append((f'beforeInitialize returns {n} bytes', b''.join([cfg(BEFORE_INIT, size=n), it(PMI, init(k, 1 << 96)),
                                                                      ext(M.pslot(k, 0))]) + end(0)))
    # B2: beforeSwap answers with a long array, then the swap allocates its structs (Pool.sol:281, 340)
    for n in (95, 96, 97, 0x10000):
        k = key(T0, T1, 3000, 60, BEFORE_SWAP)
        out.append((f'beforeSwap returns {n} bytes', b''.join([it(PMI, init(k, 1 << 96)),
                    it(PMI, M.mod(k, -600, 600, 10 ** 18)), cfg(BEFORE_SWAP, size=n),
                    it(PMI, swap(k, True, -10 ** 6, P.MIN_PRICE + 1 if hasattr(P, 'MIN_PRICE') else 4295128740)),
                    ext(M.pslot(k, 0))] + M.state(k)) + end(0)))
    # B3: a hook that reverts with n bytes of data; the wrapped error copies all of it (CustomRevert.sol:91-117)
    for n in (0, 1, 31, 32, 33, 0x8000):
        k = key(T0, T1, 3000, 60, AFTER_INIT)
        out.append((f'afterInitialize reverts with {n} bytes', b''.join([cfg(AFTER_INIT, size=n, rev=1), it(PMI, init(k, 1 << 96))]) + end(0)))
    # C1: extsload(start, n) and the shl(5, n) wrap (Extsload.sol:167-188)
    for n in (0, 1, 2, (1 << 251), (1 << 251) + 1, (1 << 251) + 2, MASK, MASK - 1):
        out.append((f'extsload range n={n:#x}', it(PMI, S['extN'] + w(0) + w(n)) + end(0)))
    # C2: array forms with a length word whose shl(5) wraps; the ABI decoder must refuse them first
    for n in (0, 1, (1 << 251), (1 << 251) + 1, 1 << 64, (1 << 64) - 1):
        out.append((f'extsload array n={n:#x}', it(PMI, S['extA'] + w(0x20) + w(n) + w(0) + w(1)) + end(0)))
        out.append((f'exttload array n={n:#x}', it(PMI, S['exttA'] + w(0x20) + w(n) + w(CUR_SLOT) + w(RES_SLOT)) + end(0)))
    # C3: sync of a currency with dirty upper bits in the calldata word (CurrencyReserves.sol:148, ABI decoder)
    for hi in (1, 1 << 95):
        out.append((f'sync dirty high bits {hi:#x}', b''.join([it(PMI, S['sync'] + w((hi << 160) | T1)), text(CUR_SLOT), text(RES_SLOT)]) + end(0)))
    return out


def reference(code, scripts):
    res = []
    for name, data in scripts:
        wd = M.world(code); wd.max_steps = 40_000_000
        try:
            ok, ret = wd.call(0, DRV, 0, data, False, 0)
            res.append(ret)
        except (TimeoutError, NotImplementedError):
            res.append(None)  # the reference has no precompiles; set A is read per network only
    return res


def ask(url, ov, data, gas=25_000_000):
    last = None
    for k in range(4):
        try:
            return bytes.fromhex(rpc(url, 'eth_call', [{'to': '0x' + DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=120)[2:])
        except Exception as e:  # noqa
            last = str(e)[:200]
            if 'gas' in last.lower() and ('limit' in last.lower() or 'cap' in last.lower() or 'allowance' in last.lower()):
                gas = 20_000_000 if gas > 20_000_000 else gas
            time.sleep(2 * (k + 1))
    return 'ERR ' + str(last)


def records(ret):
    if ret is None: return None
    if isinstance(ret, str): return ret
    return [(ok, r.hex()) for ok, r in P.parse(M.unwrap(ret))]


if __name__ == '__main__':
    outdir, mode = sys.argv[1], sys.argv[2]; only = set(map(int, sys.argv[3:]))
    code = P.fetch_code(); ov = M.overrides(code)
    nets = [n for n in networks() if not only or n[0] in only]
    if mode == 'A':
        def run(n):
            cid, name, url = n; sc = set_a(cid)
            ref = reference(code, sc)
            return cid, name, [{'script': s, 'reference': records(r), 'network': records(ask(url, ov, d))} for (s, d), r in zip(sc, ref)]
        with cf.ThreadPoolExecutor(7) as ex:
            res = list(ex.map(run, nets))
        json.dump([{'chainId': c, 'name': nm, 'runs': r} for c, nm, r in res], open(os.path.join(outdir, 'setA.json'), 'w'), indent=1)
        for c, nm, r in res:
            diff = [x['script'] for x in r if x['reference'] != x['network']]
            print(c, nm, 'scripts', len(r), 'differ from codeless reference:', len(diff), diff[:40], flush=True)
    else:
        sc = set_bc(); ref = reference(code, sc); refh = [hashlib.sha256(r).hexdigest() if r is not None else 'heavy' for r in ref]
        print('reference done', sum(1 for r in ref if r is None), 'heavy', flush=True)

        def run(n):
            cid, name, url = n; out = []
            for (s, d), h, r in zip(sc, refh, ref):
                a = ask(url, ov, d)
                ha = hashlib.sha256(a).hexdigest() if isinstance(a, bytes) else a
                out.append({'script': s, 'equal': ha == h, 'reference': records(r), 'network': records(a) if ha != h else 'same'})
            return cid, name, out
        with cf.ThreadPoolExecutor(7) as ex:
            res = list(ex.map(run, nets))
        json.dump({'scripts': [s for s, _ in sc], 'reference': [records(r) for r in ref],
                   'results': [{'chainId': c, 'name': nm, 'runs': r} for c, nm, r in res]}, open(os.path.join(outdir, 'setBC.json'), 'w'), indent=1)
        for c, nm, r in res:
            print(c, nm, 'equal', sum(x['equal'] for x in r), '/', len(r), [x['script'] for x in r if not x['equal']], flush=True)
