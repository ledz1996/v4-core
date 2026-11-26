"""Build the case list of theme-hook-and-native-sides (cycle 26). Deterministic, no random sampling (seed: none).
Usage: python3 cases26.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import *  # noqa

F = {'beforeInitialize': 1 << 13, 'afterInitialize': 1 << 12, 'beforeAddLiquidity': 1 << 11, 'afterAddLiquidity': 1 << 10,
     'beforeRemoveLiquidity': 1 << 9, 'afterRemoveLiquidity': 1 << 8, 'beforeSwap': 1 << 7, 'afterSwap': 1 << 6,
     'beforeDonate': 1 << 5, 'afterDonate': 1 << 4}
BSRD, ASRD, AALRD, ARLRD = 8, 4, 2, 1
ALLF = sum(F.values())
I128MAX = (1 << 127) - 1
I128MIN = -(1 << 127)
DYN = 0x800000
cases = []
_hk = {}


def hook_addr(flags, salt=0):
    k = (flags, salt)
    if k not in _hk: _hk[k] = (0xAB << 40) | ((len(_hk) + 1) << 14) | flags
    return _hk[k]


def toks(i):
    a = 0x7A0000000000 + 4 * i
    return a, a + 1


def bd(a0, a1): return ((a0 & ((1 << 128) - 1)) << 128) | (a1 & ((1 << 128) - 1))


def add(tag, c, cfgs, acts, settle=True, **meta):
    c = dict(c); c['id'] = len(cases); c['tag'] = tag; c['nact'] = len(acts)
    c['p'] = build_p(cfgs, acts, settle); c.update(meta)
    cases.append(c)


def pool(i, flags=None, fee=3000, native=False, hooks=None):
    t0, t1 = toks(i)
    if native: t0 = 0
    h = hooks if hooks is not None else (hook_addr(flags) if flags is not None else 0)
    return {'t0': t0, 't1': t1, 'fee': fee, 'ts': 60, 'hooks': h}


AMT_IN = -10 ** 15
AMT_OUT = 10 ** 12


def std_acts(c, zfo=True, amt=AMT_IN, extra_after=()):
    lim = MIN_SQRT + 1 if zfo else MAX_SQRT - 1
    return [(1, 0, c_init(c, 1 << 96)), (1, 0, c_mlp(c, -600, 600, 10 ** 18)), (1, 0, c_swap(c, zfo, amt, lim)),
            (1, 0, c_mlp(c, -600, 600, -5 * 10 ** 17)), (1, 0, c_donate(c, 1000, 2000))] + list(extra_after)


def ret(sel_, *words, length=None):
    b = sel_.to_bytes(4, 'big') + b'\0' * 28 + b''.join(w(x) for x in words)
    return b if length is None else (b + b'\0' * max(0, length - len(b)))[:length]


i = 0
# A. every hook function with the right selector (default) and two wrong ones, all ten function flags set
for f, s in HSEL.items():
    for wrong, tag in ((None, 'right'), (HSEL['beforeSwap'] if f != 'beforeSwap' else HSEL['afterSwap'], 'other-hook-selector'),
                       (s ^ 1, 'flipped-bit')):
        c = pool(i, ALLF); i += 1
        n = {'beforeSwap': 3, 'afterSwap': 2, 'afterAddLiquidity': 2, 'afterRemoveLiquidity': 2}.get(f, 1)
        cfg = [] if wrong is None else [(0, s, 1, ret(wrong, *([0] * (n - 1))))]
        add(f'A selector {f} {tag}', c, cfg, std_acts(c), group='A')
# B. return lengths with the correct selector in front
for f, s in HSEL.items():
    for L in (0, 4, 31, 32, 33, 64, 96, 128):
        c = pool(i, ALLF); i += 1
        add(f'B length {f} {L}', c, [(0, s, 1, ret(s, 0, 0, 0, length=L))], std_acts(c), group='B')
for f, extra in (('beforeSwap', BSRD), ('afterSwap', ASRD), ('afterAddLiquidity', AALRD), ('afterRemoveLiquidity', ARLRD)):
    for L in (32, 63, 64, 65, 96, 97):
        c = pool(i, ALLF | extra); i += 1
        add(f'B length {f}+returnsDelta {L}', c, [(0, HSEL[f], 1, ret(HSEL[f], 0, 0, 0, length=L))], std_acts(c), group='B')
# C. reverts with empty, short and long data, and a hook that consumes all forwarded gas (INVALID)
for f in HSEL:
    for d, tag in ((b'', 'empty'), (b'\xde\xad\xbe\xef', '4 bytes'), (bytes(range(31)), '31 bytes'),
                   (bytes((7 * k) & 0xff for k in range(100)), '100 bytes'), (bytes((k * 13) & 0xff for k in range(2000)), '2000 bytes')):
        c = pool(i, ALLF); i += 1
        add(f'C revert {f} {tag}', c, [(0, HSEL[f], 2, d)], std_acts(c), group='C')
    c = pool(i, ALLF); i += 1
    add(f'C allgas {f}', c, [(0, HSEL[f], 3, b'')], std_acts(c), group='C', gasHeavy=True)
# D. beforeSwap specified and unspecified deltas (beforeSwap + returnsDelta + afterSwap)
for zfo, amt in ((True, AMT_IN), (False, AMT_IN), (True, AMT_OUT), (False, AMT_OUT)):
    A = abs(amt); sgn = 1 if amt < 0 else -1  # a delta of sgn*A cancels the amount
    specs = [(sgn * A, 'zero'), (sgn * (A + 1), 'flip'), (sgn * (A - 1), 'remainder 1'), (-sgn * A, 'double'), (0, 'none'),
             (I128MAX, 'int128 max'), (I128MIN, 'int128 min')]
    for spec, st in specs:
        for unspec in (0, 12345, -12345):
            if st in ('int128 max', 'int128 min', 'double', 'none') and unspec != 0: continue
            c = pool(i, F['beforeSwap'] | BSRD | F['afterSwap']); i += 1
            add(f'D beforeSwap delta zfo={zfo} amt={amt} spec={st} unspec={unspec}', c,
                [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], bd(spec, unspec), 0))], std_acts(c, zfo, amt), group='D',
                spec=spec, unspec=unspec, amt=amt, zfo=zfo)
    for unspec in (I128MAX, I128MIN):
        c = pool(i, F['beforeSwap'] | BSRD | F['afterSwap']); i += 1
        add(f'D beforeSwap delta zfo={zfo} amt={amt} spec=0 unspec={unspec}', c,
            [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], bd(0, unspec), 0))], std_acts(c, zfo, amt), group='D',
            spec=0, unspec=unspec, amt=amt, zfo=zfo)
    # returnsDelta bit off: the same words are ignored
    c = pool(i, F['beforeSwap'] | F['afterSwap']); i += 1
    add(f'D beforeSwap delta bit off zfo={zfo} amt={amt}', c,
        [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], bd(sgn * A, 999), 0))], std_acts(c, zfo, amt), group='D',
        spec=0, unspec=0, amt=amt, zfo=zfo, bitOff=True)
    # baseline: zero delta
    c = pool(i, F['beforeSwap'] | BSRD | F['afterSwap']); i += 1
    add(f'D baseline zfo={zfo} amt={amt}', c, [], std_acts(c, zfo, amt), group='D', spec=0, unspec=0, amt=amt, zfo=zfo, baseline=True)
# E. dynamic fee override words from beforeSwap
for word, tag in ((0, '0'), (3000, '3000 no flag'), (0x400000 | 3000, 'override 3000'), (0x400000, 'override 0'),
                  (0x400000 | 1000000, 'override 1000000'), (0x400000 | 1000001, 'override 1000001'), (0xFFFFFF, '0xffffff'),
                  ((1 << 255) | 0x400000 | 500, 'dirty high bit + override 500'), ((1 << 24) | 500, 'bit 24 + 500'),
                  ((1 << 24) | 0x400000 | 500, 'bit 24 + override 500'), (0x800000 | 0x400000 | 700, 'bit 23 + override 700')):
    for amt in (AMT_IN, AMT_OUT):
        c = pool(i, F['beforeSwap'], fee=DYN); i += 1
        add(f'E dynamic fee word {tag} amt={amt}', c, [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], 0, word))],
            std_acts(c, True, amt), group='E', feeWord=word)
for word, tag in ((0x400000 | 3000, 'override 3000'), (0x400000 | 1000001, 'override 1000001')):
    c = pool(i, F['beforeSwap'], fee=3000); i += 1
    add(f'E static fee pool ignores word {tag}', c, [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], 0, word))],
        std_acts(c, True, AMT_IN), group='E', feeWord=word)
# F. afterSwap return delta
for zfo, amt in ((True, AMT_IN), (False, AMT_OUT)):
    for word, tag in ((0, '0'), (1000, '1000'), (-1000, '-1000'), (I128MAX, 'int128 max'), (I128MIN, 'int128 min'),
                      (1 << 127, '2^127'), (I128MIN - 1, '-2^127-1'), ((1 << 200) | 5, 'high bits')):
        c = pool(i, F['afterSwap'] | ASRD); i += 1
        add(f'F afterSwap delta {tag} zfo={zfo} amt={amt}', c, [(0, HSEL['afterSwap'], 1, ret(HSEL['afterSwap'], word))],
            std_acts(c, zfo, amt), group='F', word=word & M, amt=amt, zfo=zfo, baseline=(word == 0))
    c = pool(i, F['afterSwap']); i += 1
    add(f'F afterSwap delta bit off zfo={zfo}', c, [(0, HSEL['afterSwap'], 1, ret(HSEL['afterSwap'], 1000))],
        std_acts(c, zfo, amt), group='F', word=0, amt=amt, zfo=zfo, bitOff=True)
# G. afterAddLiquidity and afterRemoveLiquidity return deltas
for f, fl, rd in (('afterAddLiquidity', F['afterAddLiquidity'], AALRD), ('afterRemoveLiquidity', F['afterRemoveLiquidity'], ARLRD)):
    for (a0, a1), tag in (((0, 0), '0,0'), ((1000, -1000), '1000,-1000'), ((-1000, 1000), '-1000,1000'), ((I128MAX, 0), 'max,0'),
                          ((I128MIN, 0), 'min,0'), ((0, I128MAX), '0,max'), ((0, I128MIN), '0,min'), ((-1, -1), 'all ones')):
        c = pool(i, fl | rd); i += 1
        add(f'G {f} delta {tag}', c, [(0, HSEL[f], 1, ret(HSEL[f], bd(a0, a1)))], std_acts(c), group='G', fn=f, a0=a0, a1=a1)
    c = pool(i, fl); i += 1
    add(f'G {f} delta bit off', c, [(0, HSEL[f], 1, ret(HSEL[f], bd(1000, -1000)))], std_acts(c), group='G', fn=f, a0=0, a1=0, bitOff=True)
# H. a hook that calls back into the PoolManager from inside each hook function
for f in HSEL:
    for cbtag in ('swap', 'modifyLiquidity', 'donate', 'sync', 'take1', 'settle', 'mint', 'burn0', 'clear', 'unlock'):
        c = pool(i, ALLF); i += 1
        h = c['hooks']
        cb = {'swap': c_swap(c, False, -10 ** 9, MAX_SQRT - 1), 'modifyLiquidity': c_mlp(c, -120, 120, 10 ** 12, 7),
              'donate': c_donate(c, 5, 6), 'sync': c_sync(c['t0']), 'take1': c_take(c['t0'], h, 1), 'settle': c_settle(),
              'mint': c_mint(h, c['t1'], 3), 'burn0': c_burn(h, c['t1'], 0), 'clear': c_clear(c['t0'], 0), 'unlock': c_unlock()}[cbtag]
        add(f'H callback {cbtag} inside {f}', c, [(1, HSEL[f], 0, cb)], std_acts(c), group='H')
# I. address validation (Hooks.sol:109-127) on initialize
for flags, fee, tag in ((BSRD, 3000, 'returnsDelta without beforeSwap'), (ASRD, 3000, 'returnsDelta without afterSwap'),
                        (AALRD, 3000, 'returnsDelta without afterAdd'), (ARLRD, 3000, 'returnsDelta without afterRemove'),
                        (0, 3000, 'no flags static fee'), (0, DYN, 'no flags dynamic fee'), (ALLF | 15, 3000, 'all 14 flags'),
                        (F['beforeSwap'] | BSRD, 3000, 'beforeSwap with returnsDelta'), (0, 1000001, 'no flags fee above max')):
    c = pool(i, flags, fee=fee, hooks=hook_addr(flags, 'I')); i += 1
    add(f'I validate {tag}', c, [], [(1, 0, c_init(c, 1 << 96))], group='I')
c = pool(i, None, fee=DYN, hooks=0); i += 1
add('I validate zero hook dynamic fee', c, [], [(1, 0, c_init(c, 1 << 96))], group='I')

# ---- Task 2: native value ----
NV = 10 ** 18
# N1 native pool, hookless, full sequence; the driver settles every native debt with value
c = pool(i, native=True); i += 1
add('N1 native pool swap 0 for 1', c, [], std_acts(c, True, AMT_IN), group='N')
c = pool(i, native=True); i += 1
add('N1 native pool swap 1 for 0 exact out', c, [], std_acts(c, False, AMT_OUT), group='N')
# N2 settle with value variants (no pool needed; t1 is a token double)
c = pool(i, native=True); i += 1; t1 = c['t1']
add('N2 settle with value while ERC-20 synced', c, [], [(1, 0, c_sync(t1)), (1, 5, c_settle()), (1, 0, c_sync(0)), (1, 5, c_settle()), (1, 0, c_take(0, D, 5))], group='N')
c = pool(i, native=True); i += 1; t1 = c['t1']
add('N2 settleFor with value while ERC-20 synced', c, [], [(1, 0, c_sync(t1)), (1, 5, c_settle_for(S)), (1, 0, c_settle_for(S))], group='N')
c = pool(i, native=True); i += 1; t1 = c['t1']
add('N3 sync native after ERC-20 sync, then settle with value', c, [], [(1, 0, c_sync(t1)), (1, 0, c_sync(0)), (1, 7, c_settle()), (1, 0, c_take(0, D, 7))], group='N')
c = pool(i, native=True); i += 1
add('N4 settle with zero value and nothing synced', c, [], [(1, 0, c_settle()), (1, 0, c_settle_for(S))], group='N')
c = pool(i, native=True); i += 1; t1 = c['t1']
add('N4b ERC-20 settle after sync with nothing paid, zero value', c, [], [(1, 0, c_sync(t1)), (1, 0, c_settle())], group='N')
c = pool(i, native=True); i += 1
add('N5 settleFor S with value, S takes it', c, [], [(1, NV, c_settle_for(S)), (3, 0, c_take(0, S, NV))], group='N')
c = pool(i, native=True); i += 1
add('N5b settleFor S with value, driver tries to take it', c, [], [(1, NV, c_settle_for(S)), (1, 0, c_take(0, D, NV)), (3, 0, c_take(0, S, NV))], group='N')
c = pool(i, native=True); i += 1
add('N6 overpay then take the surplus', c, [], [(1, NV, c_settle()), (1, 0, c_take(0, D, NV - 1)), (1, 0, c_take(0, D, 1))], group='N')
c = pool(i, native=True); i += 1
add('N6b take native more than the PoolManager holds', c, [], [(1, 0, c_take(0, D, PM_BAL + 1)), (1, PM_BAL + 1, c_settle())], group='N')
c = pool(i, native=True); i += 1
add('N6c take native at int128 bound', c, [], [(1, 0, c_take(0, D, 1 << 127))], group='N')
c = pool(i, native=True); i += 1
add('N6d mint and burn native claims', c, [], [(1, NV, c_settle()), (1, 0, c_mint(D, 0, NV)), (1, 0, c_burn(D, 0, NV)), (1, 0, c_take(0, D, NV))], group='N')
# N7 native take to many recipients, amounts 1 and 0; the driver pays first with value
RECIP = [('no code 0xb0b', 0xB0B), ('rejecting contract', REJ), ('address zero', 0), ('PoolManager itself', PH_INT), ('driver', D), ('S', S)]
RECIP += [(f'precompile {k:#x}', k) for k in list(range(1, 0x12)) + [0x100]]
RECIP += [('OP L2ToL1MessagePasser', 0x4200000000000000000000000000000000000016), ('OP SequencerFeeVault', 0x4200000000000000000000000000000000000011),
          ('OP L1Block', 0x4200000000000000000000000000000000000015), ('OP WETH predeploy', 0x4200000000000000000000000000000000000006),
          ('OP BaseFeeVault', 0x4200000000000000000000000000000000000019), ('OP L2StandardBridge', 0x4200000000000000000000000000000000000010),
          ('ArbSys', 0x64), ('ArbRetryableTx', 0x6e), ('ArbOwner', 0x70), ('ArbGasInfo', 0x6c), ('NodeInterface', 0xc8),
          ('HyperEVM HYPE system', 0x2222222222222222222222222222222222222222), ('HyperEVM CoreWriter', 0x3333333333333333333333333333333333333333),
          ('HyperEVM read precompile 0x800', 0x800), ('HyperEVM read precompile 0x807', 0x807),
          ('Celo CELO token', 0x471EcE3750Da237f93B8E339c536989b8978a438), ('Celo transfer precompile 0xfd', 0xfd),
          ('Polygon MRC20 0x1010', 0x1010), ('BSC ValidatorSet / Monad staking 0x1000', 0x1000), ('BSC SystemReward 0x1002', 0x1002),
          ('Monad reserve-balance 0x1001', 0x1001), ('Avalanche NativeAssetBalance', 0x0100000000000000000000000000000000000001),
          ('Avalanche NativeAssetCall', 0x0100000000000000000000000000000000000002), ('Avalanche ContractDeployerAllowList', 0x0200000000000000000000000000000000000000),
          ('Avalanche FeeManager', 0x0200000000000000000000000000000000000003), ('Arc USDC', 0x3600000000000000000000000000000000000000),
          ('Arc 0x1800..', 0x1800000000000000000000000000000000000000), ('Tempo pathUSD', 0x20C0000000000000000000000000000000000000),
          ('Tempo fee manager', 0xfeEC000000000000000000000000000000000000), ('Tempo TIP-403 registry', 0x403C000000000000000000000000000000000000),
          ('EntryPoint v0.6', 0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789), ('EntryPoint v0.7', 0x0000000071727De22E5E9d8BAf0edAc6f37da032),
          ('EntryPoint v0.8', 0x4337084D9E255Ff0702461CF8895CE9E3b5Ff108), ('EIP-4788 beacon roots', 0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02),
          ('EIP-2935 history', 0x0000F90827F1C53a10cb7A02335B175320002935), ('EIP-7002 withdrawals', 0x00000961Ef480Eb55e80D19ad83579A64c007002),
          ('EIP-7251 consolidations', 0x0000BBdDc7CE488642fb579F8B00f3a590007251), ('Permit2', 0x000000000022D473030F116dDEE9F6B43aC78BA3)]
for name, r in RECIP:
    for amt in (1, 0):
        c = pool(i, native=True); i += 1
        add(f'N7 native take {amt} to {name}', c, [], [(1, amt, c_settle()), (1, 0, c_take(0, r, amt))], group='N7', recipient=r, amount=amt)
# N8 native pool with a hook: afterSwap returns a native delta; the hook takes native and rejects value
c = pool(i, F['afterSwap'] | ASRD, native=True); i += 1
add('N8 native pool afterSwap delta 1000 in native (exact out 1 for 0)', c, [(0, HSEL['afterSwap'], 1, ret(HSEL['afterSwap'], 1000))],
    std_acts(c, False, AMT_OUT), group='N')
c = pool(i, F['afterSwap'] | ASRD, native=True); i += 1
add('N8 native pool afterSwap delta -1000 in native', c, [(0, HSEL['afterSwap'], 1, ret(HSEL['afterSwap'], -1000))],
    std_acts(c, False, AMT_OUT), group='N')
c = pool(i, F['afterSwap'] | ASRD, native=True); i += 1
add('N8b hook that rejects value is paid its native credit', c, [(0, HSEL['afterSwap'], 1, ret(HSEL['afterSwap'], 1000)), (0, 0, 2, b'')],
    std_acts(c, False, AMT_OUT), group='N')
c = pool(i, F['afterSwap'] | ASRD, native=True); i += 1
add('N8c take native to a hook that rejects value', c, [(0, 0, 2, b'nope')], [(1, 9, c_settle()), (1, 0, c_take(0, c['hooks'], 9)), (1, 0, c_take(0, D, 9))], group='N')
c = pool(i, F['beforeSwap'] | BSRD | F['afterSwap'], native=True); i += 1
add('N8d native pool, beforeSwap takes the whole native input', c,
    [(0, HSEL['beforeSwap'], 1, ret(HSEL['beforeSwap'], bd(-AMT_IN, 0), 0))], std_acts(c, True, AMT_IN), group='N')
# N9 hook settles with value from inside its callback (hook has no balance: driver sends value through hexec)
c = pool(i, F['afterSwap'], native=True); i += 1
add('N9 settle with value through the hook and through S', c, [], [(2, 11, c_settle()), (3, 13, c_settle()), (2, 0, c_take(0, c['hooks'], 11)), (3, 0, c_take(0, S, 13))], group='N')

json.dump({'cases': cases, 'hooks': {hex(v): list(k) for k, v in _hk.items()}}, open(sys.argv[1], 'w'))
from collections import Counter
print(len(cases), Counter(c['group'] for c in cases))
