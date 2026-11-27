"""Cycle 28: one summary of the four tasks from the outputs in out/ (coverage tables, scenario results, F-130 reruns,
RPC reads). Usage: python3 -I summary28.py"""
import sys, os, json, glob, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE); sys.path.insert(0, HERE)
import blocks as B
T = {v: json.load(open(os.path.join(W, 'out', f'covtable-{v}.json'))) for v in ('0.16.5', '0.16.7')}
own = json.load(open(os.path.join(W, 'out', 'owners.json')))['reach']
diff = json.load(open(os.path.join(W, '..', '..', '027', 'theme-monad-engine-agreement.work', 'out', 'asm-blockdiff.json')))
changed = sorted(int(d['block'], 16) for d in diff['differ'])
c27 = json.load(open(os.path.join(W, '..', '..', '027', 'theme-monad-engine-agreement.work', 'out', 'cov-changed.json')))['0.16.7']['changedNotEntered']
R7 = {r['block']: r for r in T['0.16.7']['rows']}; R5 = {r['block']: r for r in T['0.16.5']['rows']}
# disposition of the 37 changed blocks no case entered before this cycle
DISP = {
 '0x878': ('transferOwnership(address): argument decode (address cleaning call)', 'decode'),
 '0x8a0': ('solmate Owned.sol:20 onlyOwner check of transferOwnership', 'compute'),
 '0x985': ('extsload(bytes32[]): call of the bytes32[] calldata decoder', 'decode'),
 '0x98d': ('Extsload.sol:44-54 result header and loop bounds', 'compute'), '0x9b0': ('Extsload.sol:55-60 loop body sload(calldataload)', 'compute'),
 '0x9c3': ('Extsload.sol:55-60 loop back edge', 'compute'),
 '0xb37': ('exttload(bytes32[]): call of the bytes32[] calldata decoder', 'decode'),
 '0xb3f': ('Exttload.sol:20-30 result header and loop bounds', 'compute'), '0xb62': ('Exttload.sol:31-36 loop body tload(calldataload)', 'compute'),
 '0xb75': ('Exttload.sol:31-36 loop back edge', 'compute'),
 '0xbae': ('protocolFeesAccrued(address): argument decode', 'decode'),
 '0xc93': ('ProtocolFees.sol:49 currency is not native, Currency.sol:107', 'compute'),
 '0xcb7': ('ProtocolFees.sol:54 amount == 0 test', 'compute'), '0xcc3': ('ProtocolFees.sol:54 read of protocolFeesAccrued[currency]', 'compute'),
 '0xcd3': ('ProtocolFees.sol:55 checked subtraction from protocolFeesAccrued', 'compute'), '0xcef': ('ProtocolFees.sol:54 amount given', 'compute'),
 '0xe89': ('setProtocolFee: PoolKey decode', 'decode'),
 '0xe99': ('ProtocolFees.sol:36 caller is protocolFeeController', 'compute'),
 '0xeba': ('ProtocolFeeLibrary.sol:27-31 isValidProtocolFee, ProtocolFees.sol:37', 'compute'),
 '0xed4': ('ProtocolFees.sol:38-40 pool id (PoolId.sol:12-15), pool slot (PoolManager.sol:388), Pool.sol:110', 'compute'),
 '0x260d': ('Extsload.sol:20-30 extsload(bytes32,uint256) header and loop bounds, shl(5, nSlots)', 'compute'),
 '0x2635': ('Extsload.sol:31-36 loop body sload(startSlot)', 'compute'), '0x2647': ('Extsload.sol:31-36 loop back edge', 'compute'),
 '0x2681': ('setProtocolFeeController(address): argument decode', 'decode'),
 '0x2c73': ('ERC6909.sol:71 interfaceId == 0x01ffc9a7', 'compute'), '0x2cab': ('ERC6909.sol:72 interfaceId == 0x0f632fb3', 'compute'),
 '0x2f7b': ('bytes32[] calldata decoder: head size check', 'decode'), '0x2fa7': ('bytes32[] decoder: offset <= 2^64-1', 'decode'),
 '0x2fb9': ('bytes32[] decoder: offset + 0x23 < calldatasize', 'decode'), '0x2fc4': ('bytes32[] decoder: length <= 2^64-1', 'decode'),
 '0x2fd9': ('bytes32[] decoder: end within calldata', 'decode'), '0x2fe7': ('bytes32[] decoder: returns offset and length', 'decode'),
 '0x3aae': ('Currency.sol:92 address(this).balance in balanceOfSelf', 'unreachable: both callers (PoolManager.sol:285 and :359) exclude address(0) first (PoolManager.sol:281, :352)'),
 '0x40d7': ('Hooks.sol:137 bytes4(data) for hook calldata shorter than 4 bytes, inside the HookCallFailed revert data', 'revert data, and unreachable: hook calldata is an abi.encodeCall of at least 4 bytes'),
 '0x593c': ('FullMath.sol:33-37 prod1 == 0 return of the mulDiv copy called only from SqrtPriceMath.sol:97', 'unreachable: line 97 runs only for amount > 2^160, so amount * 2^96 >= 2^256 + 2^96 and prod1 >= 1'),
 '0x5b2e': ('SqrtPriceMath.sol:194 swap of the two prices (round-up copy)', 'unreachable: every caller passes the lower price first (SwapMath.sol:66-67, 85-86, 91-92, 101-102; Pool.sol modifyLiquidity)'),
 '0x5bd5': ('SqrtPriceMath.sol:194 swap of the two prices (round-down copy)', 'unreachable: as 0x5b2e'),
}
REM = {
 '0x1eb1': 'Panic 0x41 of the memory allocator; the free memory pointer never passes 2^64. Revert data only, unreachable',
 '0x3aae': DISP['0x3aae'][1], '0x3af7': 'Currency.sol:94 zero result when staticcall failed; the failure already reverted at 0x3aed. Unreachable',
 '0x40d7': DISP['0x40d7'][1], '0x449e': 'TickMath.sol:70 InvalidTick revert; checkTicks (Pool.sol:94-98) and the swap clamps (Pool.sol:351-356) keep ticks in range. Revert data only, unreachable',
 '0x492c': 'Panic 0x12 division by zero in the checked division helper (ProtocolFeeLibrary.sol:15 denominator) and mulDivRoundingUp copies (FullMath.sol:112); every denominator is a nonzero constant or already passed require(denominator > prod1). Revert data only, unreachable',
 '0x5061': 'SqrtPriceMath.sol:135-143 InvalidPriceOrLiquidity; computeSwapStep calls getNextSqrtPrice only when the step stops short, which needs liquidity > 0. Revert data only, unreachable',
 '0x518f': 'SqrtPriceMath.sol:109-114 NotEnoughLiquidity; the step stops short only when the output is below the output to the target, so the quotient stays below the price. Revert data only, unreachable',
 '0x51ec': 'FullMath.sol:113 require(++result > 0) in the copy at SqrtPriceMath.sol:105; result 2^256-1 would need amount*2^96 >= L*(2^256-1) with prod1 < L, no integer amount below 2^255 fits. Revert data only, unreachable',
 '0x593c': DISP['0x593c'][1], '0x5b22': 'SqrtPriceMath.sol:197-202 InvalidPrice for a zero price; prices are at least MIN_SQRT_PRICE. Revert data only, unreachable',
 '0x5b2e': DISP['0x5b2e'][1], '0x5bd5': DISP['0x5bd5'][1],
 '0x5cf5': 'SqrtPriceMath.sol:59-69 PriceOverflow in the output copy; the step stops short only when amount < amount to target < numerator1/sqrtP, so the product never reaches numerator1. Revert data only, unreachable',
 '0x5d02': 'SqrtPriceMath.sol:37 amount == 0 in the output copy; exact-output steps pass amountRemaining > 0 (Pool.sol loop runs while it is nonzero). Unreachable',
}
def entered_by(b):
    r = R7[b]; return sorted(k for k, v in r['entered'].items() if v)
t3 = []
for o in changed:
    h = hex(o)
    if h not in c27: continue
    src, disp = DISP[h]
    t3.append({'block': h, 'source': src, 'disposition': disp, 'functions': own.get(h, []), 'enteredNowBy167': entered_by(h),
               'enteredNowBy165': sorted(k for k, v in R5[h]['entered'].items() if v)})
t4 = [{'block': b, 'src': R7[b]['src'], 'changed167': R7[b]['changed167'], 'why': REM[b]} for b in T['0.16.7']['notEntered']]
F130 = json.load(open(os.path.join(W, 'out', 'f130-entering.json')))
tg = {'SqrtPriceMath.sol:52': ['0x5d5d', '0x5d6c', '0x5d71'], 'SqrtPriceMath.sol:97': ['0x503a', '0x505c', '0x588a', '0x58d6', '0x58db', '0x593c', '0x330'],
      'SqrtPriceMath.sol:105': ['0x519c', '0x51cf', '0x51e4', '0x5943', '0x5981', '0x5986', '0x59da', '0x51ec', '0x492c'],
      'Position.sol:94-96': ['0x173e', '0x1755', '0x1761', '0x5703', '0x5752', '0x5757', '0x577c']}
t2 = {k: [{'block': b, 'src': R7[b]['src'][:4], 'enteredBy': entered_by(b)} for b in v] for k, v in tg.items()}
S = json.load(open(os.path.join(W, 'out', 's28', 'results.json')))['results']
S.update(json.load(open(os.path.join(W, 'out', 's28e', 'results.json')))['results']); S.update(json.load(open(os.path.join(W, 'out', 's28f', 'results.json')))['results'])
scen = {k: {v: {'engineSame': x[v]['engineSame'], 'interpVsRef': x[v]['interpVsRef'], 'nativeVsRef': x[v]['nativeVsRef']} for v in ('0.16.5', '0.16.7')} | {'ntx': x['ntx']} for k, x in S.items()}
sha = {v: {b: hashlib.sha256(open(os.path.join(W, 'build', v, b), 'rb').read()).hexdigest() for b in ('hxf', 'hxfcov')} for v in ('0.16.5', '0.16.7')}
vg = sorted(set(l.split('==', 2)[-1].strip() for f in glob.glob(os.path.join(W, 'out', 'vg', 'vg-*.log')) for l in open(f) if 'ERROR SUMMARY' in l))
out = {'task1': {'binaries': sha, 'valgrindRuns': len(glob.glob(os.path.join(W, 'out', 'vg', 'vg-*.log'))), 'valgrindSummaries': vg,
                 'coverage': {v: {k: T[v][k] for k in ('blocks', 'files', 'enteredBySet', 'enteredAny')} | {'notEntered': len(T[v]['notEntered'])} for v in T}},
       'task2': t2, 'task2Cases': F130, 'task3': t3, 'task4': t4, 'scenarios': scen}
json.dump(out, open(os.path.join(W, 'out', 'summary.json'), 'w'), indent=1)
print(json.dumps(out['task1'], indent=0)[:1500]); print(len(t3), 'task3 rows;', sum(1 for r in t3 if r['enteredNowBy167']), 'entered now;', len(t4), 'never entered')
for r in t3: print(r['block'], r['disposition'][:40], r['enteredNowBy167'])
print(all(s['0.16.5']['engineSame'] and s['0.16.7']['engineSame'] and not any(s[v][k] for v in ('0.16.5', '0.16.7') for k in ('interpVsRef', 'nativeVsRef')) for s in scen.values()), len(scen))
