"""Write cycles/024/theme-producer-branch-coverage.research.json from the outputs in ../out."""
import json, os, ast, glob
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + '/../out'
NR = '/home/user/v4-core/research/network-risk'
WD = 'research/network-risk/cycles/024/theme-producer-branch-coverage.work'
T1 = json.load(open(OUT + '/task1-summary.json'))
T2 = json.load(open(OUT + '/task2.json'))
ALL = [n['chainId'] for n in json.load(open(NR + '/state/networks.json'))['networks']]

def mut(cid):
    """merge mutation results: first-run log lines (none, amountOut +1), split runs, wordCross runs"""
    res = {}
    full = OUT + '/%d/mutation-subset.json' % cid
    if os.path.exists(full): res.update(json.load(open(full))['mutations'])
    first = OUT + '/log-mut-%d-first.txt' % cid
    if os.path.exists(first):
        for line in open(first):
            name, rest = line.split(' {', 1); res[name] = ast.literal_eval('{' + rest)
    for f in glob.glob(OUT + '/%d/mutation-subset-*.json' % cid) + glob.glob(OUT + '/%d/mutation-subsetwordCross*.json' % cid):
        for k, v in json.load(open(f))['mutations'].items(): res.setdefault(k, {}).update(v)
    return res
M = {c: mut(c) for c in (8453, 143, 4326)}
def rate(c, m, cat):
    e = M[c].get(m, {}).get(cat)
    return '%d/%d' % (e['detected'], e['txs']) if e else 'n/a'
NAMES = {8453: 'Base', 143: 'Monad', 4326: 'MegaETH'}
def mut_text():
    parts = []
    for c in (8453, 143, 4326):
        p = []
        for m, cat in (('flipTick wrong bit', 'flip'), ('getAmount0Delta round-up +1', 'roundUp'), ('new: mulDivRoundingUp without increment', 'roundUp'),
                       ('new: getNextSqrtPriceFromAmount0RoundingUp -1', 'roundUp'), ('new: getAmount1Delta round-up dropped', 'roundUp'),
                       ('new: uninitialized word edge one spacing inside', 'wordCross'), ('new: uninitialized word edge one spacing inside', 'wordEdge'),
                       ('getTickAtSqrtPrice +1 on 1/7 of prices', 'wordCross'), ('swap amountOut +1', 'wordCross'), ('none', 'flip'), ('none', 'roundUp'), ('none', 'wordCross')):
            p.append('%s on %s %s' % (m.replace('new: ', ''), cat, rate(c, m, cat)))
        pop = {}
        for f in glob.glob(OUT + '/%d/mutation-subset*.json' % c): pop.update(json.load(open(f))['population'])
        parts.append('%s (transactions in each category: %s): %s.' % (NAMES[c], ', '.join('%s %d' % kv for kv in sorted(pop.items())), '; '.join(p)))
    return ' '.join(parts)
def pc(cid, key): return T2[key][str(cid)]

t1 = {c: T1[str(c)] for c in (143, 4326, 999, 8453)}
replay_line = ('pyevm_cov.py (tools/opdiff/pyevm.py with a per-side JUMPI counter and operand watch points added) reran every PoolManager frame of the transactions cycle 23 traced, '
               'answering outgoing calls from the recorded call tree: Monad %d transactions, %d frames, %d steps; MegaETH %d, %d, %d; HyperEVM %d, %d, %d (its whole PoolManager history to block 52,268,606); Base %d, %d, %d. '
               'Every frame gave the recorded success flag and return data, every outgoing call had the recorded target, value and calldata, and the storage written equals the diffMode post state in every transaction. '
               'The one exception is the HyperEVM deployment transaction 0x886b45bc, whose CREATE2 constructor write of the owner slot the frame rerun does not model.') % (
    t1[143]['txs'], t1[143]['frames'], t1[143]['steps'], t1[4326]['txs'], t1[4326]['frames'], t1[4326]['steps'], t1[999]['txs'], t1[999]['frames'], t1[999]['steps'],
    t1[8453]['txs'], t1[8453]['frames'], t1[8453]['steps'])
jump_line = ('Of the 387 conditional jumps of the build, the producers executed both sides of %d on Monad, %d on MegaETH and %d on HyperEVM (Base %d); one side only of %d, %d and %d (Base %d); '
             'never %d, %d and %d (Base %d). Of the one-sided jumps, the missing side ends in REVERT in %d, %d and %d cases, which is expected because the windows hold only successful transactions; '
             'the missing side computes something in %d, %d and %d cases.') % (
    t1[143]['both'], t1[4326]['both'], t1[999]['both'], t1[8453]['both'], t1[143]['oneSide'], t1[4326]['oneSide'], t1[999]['oneSide'], t1[8453]['oneSide'],
    t1[143]['never'], t1[4326]['never'], t1[999]['never'], t1[8453]['never'],
    t1[143]['oneSideMissingSideReverts'], t1[4326]['oneSideMissingSideReverts'], t1[999]['oneSideMissingSideReverts'],
    t1[143]['oneSideMissingSideComputes'], t1[4326]['oneSideMissingSideComputes'], t1[999]['oneSideMissingSideComputes'])

def jl(c):
    t = t1[c]
    return ('of the 387 conditional jumps of the build the producer executed both sides of %d, one side only of %d (the missing side reverts in %d of them and computes in %d) and neither side of %d'
            % (t['both'], t['oneSide'], t['oneSideMissingSideReverts'], t['oneSideMissingSideComputes'], t['never']))
common_untested = (
    'Never executed by any of the three producers in the windows: Pool.donate and PoolManager.donate (src/libraries/Pool.sol:466-480); PoolManager.clear (src/PoolManager.sol:310-319, never on Base either); '
    'settleFor (src/PoolManager.sol:305-307); ERC6909 transfer, transferFrom, approve and the third-party allowance branch of _burnFrom (src/ERC6909.sol:25-56, src/ERC6909Claims.sol:15-19); '
    'the 512-bit path (prod1 != 0) of four of the five compiled copies of FullMath.mulDiv: the Position fee copy (src/libraries/Position.sol:94-96, entry pc 22275), the exact-input fee copy (src/libraries/SwapMath.sol:65, pc 22405, once on Base with amountRemaining 2^255-1), '
    'the getAmount1Delta copy (src/libraries/SqrtPriceMath.sol:250, pc 22544) and the amount > uint160 copy (src/libraries/SqrtPriceMath.sol:97, pc 22666), plus mulDivRoundingUp(amount, Q96, liquidity) at src/libraries/SqrtPriceMath.sol:105 (pcs 20931-20971); '
    'the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp (src/libraries/SqrtPriceMath.sol:43 false, :45 false and the divRoundingUp at :52); the clamp step.tickNext <= MIN_TICK (src/libraries/Pool.sol:351) and getTickAtSqrtPrice within 2^16 of MIN_SQRT_PRICE (src/libraries/TickMath.sol:127, window data); '
    'the protocol fee branch (src/libraries/Pool.sol:385-398, src/PoolManager.sol:238, ProtocolFeeLibrary.calculateSwapFee); and the 100 percent fee branch (src/libraries/Pool.sol:311).')

findings = [
 {"ref": "F-118", "title": "MegaETH's closed producer has never executed several PoolManager branch sides that an ordinary account can reach",
  "chainIds": [4326], "lens": "L1", "assumptions": ["A10"], "effect": "both", "actor": "operator", "severity": "info",
  "difference": "MegaETH blocks are written by a closed JIT executor (F-118). The only evidence about it is what it mined. This unit lists what it mined at the level of branch sides and operands.",
  "mechanism": replay_line.split(' Every frame')[0] + ' On MegaETH, ' + jl(4326) + '. ' + common_untested +
      ' Outside the window, eth_getLogs over the whole chain (blocks 0 to 32,890,347) found no Donate event and no ERC-6909 Transfer, Approval or OperatorSet event other than 47 mints and 140 self burns, so donate, ERC-6909 transfers, approvals and operator changes have never run on the MegaETH producer. '
      'Six swaps before the window end at the bounds (blocks 15,985,054 to 28,081,792, sqrt price MIN+1 or MAX-1, or tick 489,854). Rerun from their own traces through pyevm_cov and through cycle 23 model.py they match in every frame and storage word, and they took Pool.sol:351 once and Pool.sol:354 four times, and getTickAtSqrtPrice within 2^16 of both bounds. '
      'So on MegaETH the MIN and MAX clamps have been executed by the producer, and the untested list reduces to donate, clear, settleFor, ERC-6909 transfers and allowances, the four FullMath 512-bit copies, mulDivRoundingUp at SqrtPriceMath.sol:105, the getNextSqrtPriceFromAmount0RoundingUp overflow fallback, the protocol fee branch and the 100 percent fee branch. '
      'BitMath saw 81 of 256 most significant bit results and 70 of 256 least significant bit results, none above bit 242; flipTick never ran at bitPos 255 or at a negative compressed tick with bitPos 0.',
  "impact": "No fault was found. If the producer computed one of these sides wrongly, the first transaction to take it would be executed with that result. Donate, settleFor, the ERC-6909 allowance checks and the getNextSqrtPriceFromAmount0RoundingUp fallback decide balances or claims of other users. An ordinary account can reach them in a pool it does not own (donate of 1 wei, a settleFor naming another recipient, transferFrom of someone else's claim, a dust position at a chosen tick to set a chosen bitmap bit).",
  "preconditions": "A fault in the closed MegaETH executor on one of the listed paths. None is known. The path must then be taken by a transaction, which any account can send.",
  "mitigations": "Before deployment, the deployer can send one transaction per untested path on MegaETH in a pool of its own (donate, clear, settleFor, ERC-6909 transfer, transferFrom, approve, setOperator, a swap at a price above 2^129 with amount0 large enough to overflow amount * sqrtPrice, and an exact-input swap with amountSpecified near type(int256).min) and compare the mined receipt and storage with the source model.",
  "coreRefs": ["src/libraries/Pool.sol:466-480", "src/PoolManager.sol:305-319", "src/ERC6909.sol:25-56", "src/ERC6909Claims.sol:15-19", "src/libraries/FullMath.sol:33-100", "src/libraries/SqrtPriceMath.sol:37-74", "src/libraries/SqrtPriceMath.sol:93-106", "src/libraries/Pool.sol:351-356", "src/libraries/Pool.sol:385-398"],
  "sources": [
    {"url": "https://mainnet.megaeth.com/rpc", "supports": "eth_getCode of 0xacb7e78f...d38e at latest is 24,009 bytes and equals build/PoolManager.json runtime with its immutable set to that address (mega-reth/v2.3.1-4499c42@mnet-ash-rpc-2 before and after, 2026-11-26T09:46Z, out/codecheck.json)."},
    {"url": "https://mainnet.megaeth.com/rpc", "supports": "eth_getLogs on the PoolManager for Donate over blocks 0 to 32,890,347 returned 0 logs; for ERC-6909 Transfer, Approval and OperatorSet 187 logs, 47 mints and 140 burns by the owner; for Initialize 143 pools, none with static fee 1,000,000 (out/logs-4326-*.json, out/megaeth-6909.json, chainq.jsonl)."},
    {"url": "https://mainnet.megaeth.com/rpc", "supports": "debug_traceTransaction (prestateTracer, diffMode, callTracer) of 0x44659f59..., 0xfb406db3..., 0x35ba65ae..., 0x5b17003c..., 0x2d6c6401..., 0x08dfda7b...; rerun with no mismatch (raw/4326, out/4326/extra-shard0.json, raw/4326/model-result.json)."},
    {"url": WD + "/out/4326/branches.json:1", "supports": "per-side JUMPI counts with source lines for the 20,000 MegaETH transactions"},
    {"url": WD + "/out/task2.json:1", "supports": "counts and operand ranges of the arithmetic sites"},
    {"url": "src/libraries/Pool.sol:385", "supports": "the protocol fee branch runs only when slot0 protocolFee is nonzero"}],
  "evidence": "primary"},
 {"ref": "F-130", "title": "Monad's producers have never executed several PoolManager branch sides that an ordinary account can reach",
  "chainIds": [143], "lens": "L1", "assumptions": ["A10"], "effect": "both", "actor": "operator", "severity": "info",
  "difference": "Monad validators run frequently used contracts as compiled native code, and public trace endpoints run the interpreter only (F-130). The mined replay shows which branch sides the network committed results for.",
  "mechanism": 'On Monad, ' + jl(143) + ' (window of 20,000 transactions, blocks 125,440,776 to 125,484,771). ' + common_untested +
      ' In addition the producers never took the clamp step.tickNext >= MAX_TICK (src/libraries/Pool.sol:354) and never ran getTickAtSqrtPrice within 2^16 of either price bound. '
      'Swap logs of the 200,000 blocks before the window (125,240,776 to 125,440,775, 249,215 swaps) hold no swap ending within 25,600 ticks or 2^16 of a price bound, none at sqrt price 2^129 or above and no pool liquidity at 2^96 or above, and no Donate event. '
      'eth_getLogs on every public Monad endpoint tried refuses ranges over 100 blocks, so the 125 million earlier blocks were not searched. '
      'BitMath saw 102 of 256 most significant bit results and 100 of 256 least significant bit results; flipTick never ran at bitPos 255. '
      'Cycle 23 theme-monad-compiled-coverage entered 899 of 913 compiled blocks in the compiler harness with test inputs, so the compiled code of these paths has run on the compiler, but not on a validator for a mined transaction.',
  "impact": "No fault was found. A fault on a listed side would first show when a transaction takes it. Donate, settleFor, the ERC-6909 allowance checks, the MAX clamp and the getNextSqrtPriceFromAmount0RoundingUp fallback decide balances or claims of other users and are reachable by an ordinary account in pools it does not own.",
  "preconditions": "A fault in the compiled execution of one of the listed paths. None is known.",
  "mitigations": "Same canary transactions as for MegaETH, sent on Monad so that validators execute each side with their compiled code before user funds arrive.",
  "coreRefs": ["src/libraries/Pool.sol:351-356", "src/libraries/Pool.sol:466-480", "src/PoolManager.sol:305-319", "src/ERC6909.sol:35-48", "src/libraries/SqrtPriceMath.sol:37-52", "src/libraries/FullMath.sol:33-100"],
  "sources": [
    {"url": "https://rpc.monad.xyz", "supports": "eth_getCode of 0x188d586d...a8e is 24,009 bytes equal to the build with its immutable (Monad/0.16.7 before and after, out/codecheck.json); eth_getLogs swap scan 125,340,776 to 125,440,775 (110,275 logs) and Donate scan 125,240,776 to 125,440,775 (0 logs); a 1,000 block range is refused with 'block range too large'."},
    {"url": "https://rpc-mainnet.monadinfra.com", "supports": "eth_getLogs swap scan 125,240,776 to 125,340,775 (138,940 logs), Monad/0.16.7 before and after; 10,000 block range refused."},
    {"url": WD + "/out/143/branches.json:1", "supports": "per-side JUMPI counts for the 20,000 Monad transactions"},
    {"url": "src/libraries/Pool.sol:354", "supports": "MAX_TICK clamp"}],
  "evidence": "primary"},
 {"ref": "F-120", "title": "HyperEVM's closed validator has never executed an exact-output swap or a donate in the PoolManager's whole history",
  "chainIds": [999], "lens": "L1", "assumptions": ["A10"], "effect": "both", "actor": "operator", "severity": "info",
  "difference": "HyperEVM blocks come from a closed validator and carry no usable state root (F-120). Cycle 23 traced the PoolManager's whole history with logs, 2,833 transactions from deployment at block 45,998,366 to 52,268,606, and no PoolManager log appeared from 52,268,607 to 52,287,517.",
  "mechanism": 'On HyperEVM, ' + jl(999) + '. ' + common_untested +
      ' Beyond that list, HyperEVM never ran an exact-output swap: SwapMath.computeSwapStep lines 88-104 (pcs 20618, 20638, 20672), getNextSqrtPriceFromOutput (src/libraries/SqrtPriceMath.sol:158-178), the subtract side of getNextSqrtPriceFromAmount1RoundingDown (:102-118, divRoundingUp at :104 and the NotEnoughLiquidity check at :109) and the subtract side of getNextSqrtPriceFromAmount0RoundingUp (:54-72) have 0 executions. '
      'It took the MAX clamp 8 times and getTickAtSqrtPrice within 2^16 of MAX_SQRT_PRICE 8 times, never the MIN side. BitMath saw 85 of 256 most significant bit results and 44 of 256 least significant bit results; the lte search never started at a negative compressed tick with bitPos 0, and flipTick never ran at a negative compressed tick with bitPos 0 or a nonnegative one with bitPos 255.',
  "impact": "No fault was found. Exact-output swaps are a standard router mode, so the first ordinary user to send one on HyperEVM is the first execution of that code on the validator, in a pool of other users' liquidity. The output path decides how much input the swapper pays (amountIn rounded up at SwapMath.sol:100-104) and how far the price moves.",
  "preconditions": "A fault in the closed validator on the exact-output or donate paths. None is known; the replicas and eth_call on rpc.hyperliquid.xyz/evm computed these paths correctly in earlier cycles, and whether that endpoint runs the block-producing EVM is unknown (cycle 23 critic).",
  "mitigations": "The deployer can send an exact-output swap, a donate, a clear, a settleFor and an ERC-6909 transferFrom on HyperEVM in its own pool before announcing it, and compare the receipt and the later storage read with the source model.",
  "coreRefs": ["src/libraries/SwapMath.sol:87-105", "src/libraries/SqrtPriceMath.sol:54-72", "src/libraries/SqrtPriceMath.sol:101-118", "src/libraries/SqrtPriceMath.sol:158-178", "src/libraries/Pool.sol:466-480"],
  "sources": [
    {"url": "https://rpc.hyperliquid.xyz/evm", "supports": "eth_getCode of 0x12D4Fd9C...6B1F equals the build with its immutable (hyperliquid evm Mainnet before and after, 2026-11-26T09:46Z); slot 2 (protocolFeeController) is zero."},
    {"url": "https://rpc.purroofgroup.com", "supports": "eth_getLogs on the PoolManager for every topic over 52,268,607 to 52,287,517 returned 0 logs (reth/v0.1.0-f0cad31 before and after)."},
    {"url": WD + "/out/999/branches.json:1", "supports": "per-side JUMPI counts for all 2,833 HyperEVM transactions; SwapMath.sol:88 JUMPI 20618 has 0 executions"},
    {"url": "src/libraries/SwapMath.sol:88", "supports": "exact-output branch of computeSwapStep"}],
  "evidence": "primary"},
]

cleared = [
 {"chainIds": [143, 4326, 999, 8453], "lens": "L1", "check": "Task 1: every PoolManager frame of the 62,820 transactions that cycle 23 traced on Monad, MegaETH, HyperEVM and Base, rerun instruction by instruction in a copy of the reference interpreter with per-side JUMPI counters, from the recorded prestate, against the recorded frames and the diffMode post state.",
  "result": replay_line + ' ' + jump_line + ' Since storage, return data and every outgoing call equal what the chain recorded, the producers took the same path as the interpreter on each of these sides.',
  "source": WD + "/scripts/replaycov.py:1 and out/<chainId>/branches.json, out/task1-summary.json"},
 {"chainIds": [143, 4326, 999], "lens": "L1", "check": "Task 2: arithmetic sites that the producers did execute, with operand ranges (out/task2.json).",
  "result": ('FullMath.mulDiv general copy (entry pc 22851, used by getAmount0Delta and mulDivRoundingUp) took prod1 != 0 %s times on Monad, %s on MegaETH and %s on HyperEVM, with the remainder MULMOD at pc 22921 executed as often (first operand up to 182 bits, denominator 96 to 182 bits). '
             'The round-up increment of mulDivRoundingUp (pc 23682) ran %s, %s and %s times and the exact case %s, %s and %s times. getAmount1Delta round-up MULMOD (pc 23094) ran on all three. '
             'getSqrtPriceAtTick ran with negative ticks %s, %s and %s times and with |tick| above 821,736 %s, %s and %s times (SAR and SIGNEXTEND at TickMath.sol:60). '
             'TickBitmap.position after compress ran at negative and nonnegative compressed ticks with bitPos 0 and 255 in both searches on Monad and MegaETH (HyperEVM lacks only the lte search at a negative tick with bitPos 0). '
             'LiquidityMath.addDelta ran with a negative delta %s, %s and %s times. BalanceDelta SAR unpacking ran with negative amount0 on all three. getNextSqrtPriceFromAmount0RoundingUp add took the non-overflow branch every time (%s, %s, %s).') % (
      pc(143, list(T2)[0])[1], pc(4326, list(T2)[0])[1], pc(999, list(T2)[0])[1],
      T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['143'][0], T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['4326'][0], T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['999'][0],
      T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['143'][1], T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['4326'][1], T2[[k for k in T2 if k.startswith('mulDivRoundingUp FullMath')][0]]['999'][1],
      T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick SAR')][0]]['143'].get('tickNeg', 0), T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick SAR')][0]]['4326'].get('tickNeg', 0), T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick SAR')][0]]['999'].get('tickNeg', 0),
      T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick GT')][0]]['143'].get('absTick>821736', 0), T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick GT')][0]]['4326'].get('absTick>821736', 0), T2[[k for k in T2 if k.startswith('getSqrtPriceAtTick GT')][0]]['999'].get('absTick>821736', 0),
      T2[[k for k in T2 if k.startswith('LiquidityMath.addDelta')][0]]['143'].get('yNeg', 0), T2[[k for k in T2 if k.startswith('LiquidityMath.addDelta')][0]]['4326'].get('yNeg', 0), T2[[k for k in T2 if k.startswith('LiquidityMath.addDelta')][0]]['999'].get('yNeg', 0),
      T2[[k for k in T2 if 'SqrtPriceMath.sol:43' in k][0]]['143'][0], T2[[k for k in T2 if 'SqrtPriceMath.sol:43' in k][0]]['4326'][0], T2[[k for k in T2 if 'SqrtPriceMath.sol:43' in k][0]]['999'][0]),
  "source": WD + "/out/task2.json:1"},
 {"chainIds": ALL, "lens": "L1", "check": "Whether the 512-bit paths of the Position fee copy of mulDiv (Position.sol:94-96), the amount > uint160 copy (SqrtPriceMath.sol:97) and mulDivRoundingUp at SqrtPriceMath.sol:105, which no producer has executed, can decide a balance.",
  "result": "They cannot. The Position copy takes prod1 != 0 only when the fee owed is at least 2^128, and Pool.sol:192 then reverts in toInt128 (SafeCast.sol:56-58). The two SqrtPriceMath sites need an amount above 2^160 in a step that exhausts the remaining amount (SwapMath.sol:75-82 and 94-98), so params.amountSpecified - amountSpecifiedRemaining equals amountSpecified and Pool.sol:455 or :459 reverts in toInt128 (SafeCast.sol:40-43). Their results are therefore only ever computed in transactions that revert. The exact-input fee copy (SwapMath.sol:65) takes the 512-bit path only for |amountRemaining| near 2^236 or more; its result is only compared with amountIn, and any value below amountIn leads to the same revert at Pool.sol:455 or :459.",
  "source": "src/libraries/Pool.sol:192, src/libraries/Pool.sol:453-461, src/libraries/SwapMath.sol:63-83"},
 {"chainIds": [143, 4326, 999], "lens": "L1", "check": "Whether an ordinary account can reach the protocol fee branch (Pool.sol:385-398, PoolManager.sol:238, ProtocolFeeLibrary.calculateSwapFee) that no producer of the three has executed.",
  "result": "No. eth_getStorageAt slot 2 of the PoolManager (protocolFeeController) is zero on all three at the latest block, so only the owner can first appoint a controller, which then sets fees (src/ProtocolFees.sol:28-40). The branch needs governance.",
  "source": "https://rpc.monad.xyz, https://mainnet.megaeth.com/rpc, https://rpc.hyperliquid.xyz/evm (out/chainq.jsonl step pfc, 2026-11-26T10:02Z)"},
 {"chainIds": [8453, 143, 4326], "lens": "L1", "check": "Task 4 (L-1040): one-unit mutations of cycle 23 mutate.py and four new ones rerun on replayed transactions selected by branch: flip (flipTick ran), roundUp (mulDivRoundingUp incremented), wordEdge (the search returned an uninitialized word edge) and wordCross (Pool.sol:415 not initialized, so a step ended on that edge and the swap went on). Sampling random.Random(20261126 + chainId), up to 300 per category (200 for wordCross).",
  "result": mut_text() + ' The unmutated model gives zero mismatches on every subset. On the targeted subsets the wrong bitmap bit is seen in 299 to 300 of 300, 46 of 46 and 149 of 149 flip transactions, the dropped mulDivRoundingUp increment in 295 to 299 of 300 roundUp transactions, and the moved word edge in 200 of 200 wordCross transactions on Base and MegaETH and 133 of 200 on Monad. On wordEdge, where the search returned an edge that the swap did not reach, the moved edge is seen in 7 to 50 of 300, as expected, since the target price of a step that ends early does not enter its result. The cycle 23 change to getAmount0Delta(roundUp) stays low even on the roundUp subset, because exact-input swaps that exhaust their amount in one step never use the rounded-up amountIn (SwapMath.sol:69-83); the same holds for getAmount1Delta round-up.',
  "source": WD + "/scripts/mutate_subset.py:1 and out/<chainId>/mutation-subset*.json"},
 {"chainIds": [4326], "lens": "L1", "check": "Task 3 on MegaETH: mined swaps outside the replay window that take the MIN and MAX tick clamps or end near the price bounds, rerun through pyevm_cov and cycle 23 model.py.",
  "result": "Six swaps found in 33,426 Swap logs of blocks 8,097,067 to 28,351,387 (ticks -887,272, 887,271 four times and 489,854). All six rerun with no frame, call or storage difference in pyevm_cov and no mismatch in model.py. They executed Pool.sol:351 once, Pool.sol:354 four times and getTickAtSqrtPrice within 2^16 of both price bounds.",
  "source": "https://mainnet.megaeth.com/rpc (debug_traceTransaction of the six; " + WD + "/raw/4326/model-result.json)"},
]

leads = [
 {"chainIds": [143], "lens": "L1", "question": "Is there a public Monad log index (explorer or indexer API without a key) that lists every Donate, ERC-6909 Transfer and Approval event and every swap ending near a price bound on 0x188d586d...a8e since deployment?", "why": "Public Monad endpoints refuse eth_getLogs ranges over 100 blocks, so only 244,000 recent blocks were searched for mined evidence of the sides the Monad producers have not executed in the window.", "priority": "low"},
 {"chainIds": ALL, "lens": "L1", "question": "Does the PoolManager on any of the 21 networks hold at least 2^96 units of a token, so that an ordinary account could borrow it with take and drive the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp (SqrtPriceMath.sol:43-52) in a hookless pool priced above sqrt price 2^129?", "why": "No producer and no mined swap on Monad, MegaETH, HyperEVM or Base has executed that fallback, and its result sets the price after an exact-input zeroForOne step, so it decides other users' output.", "priority": "medium"},
 {"chainIds": [4326], "lens": "L1", "question": "Do the MegaETH stateless-validator blocks since cycle 19 contain PoolManager transactions outside the 20,000 replayed here, and which branch sides do they add?", "why": "L-1030 asked for these as well; this unit used only the replayed traces and six fetched transactions.", "priority": "low"},
]
leadResults = [
 {"leadId": "L-1030", "outcome": "inconclusive", "answer": "Measured on MegaETH (F-118 entry above): " + jl(4326) + '. The missing sides that compute something are donate, clear, settleFor, ERC-6909 transfers and allowances, four FullMath 512-bit copies and mulDivRoundingUp at SqrtPriceMath.sol:105 (only reachable in reverting calls), the getNextSqrtPriceFromAmount0RoundingUp overflow fallback (reachable in a successful exact-input swap only above sqrt price 2^129 with amount0 of at least 2^256 / sqrtPrice), the protocol fee branch (governance only) and the 100 percent fee branch. The MIN and MAX clamps and getTickAtSqrtPrice within 2^16 of both bounds were executed by the producer in six pre-window swaps that replay exactly. The compress path of TickBitmap.position ran at negative ticks with bitPos 0 and 255. BitMath saw 81 msb and 70 lsb results of 256, none above bit 242. No fault was seen. The stateless-validator blocks were not read.'},
 {"leadId": "L-1040", "outcome": "cleared", "answer": "Yes for flipTick: on the flip subsets a wrong bitmap bit is detected in 299 of 300 (Base), 46 of 46 (Monad) and 149 of 149 (MegaETH) transactions, against 1 to 5 of 300 on random samples. No for getAmount0Delta(roundUp) +1: 56, 73 and 45 of 300 on the roundUp subsets, because single-step exact-input swaps never use the rounded-up amountIn; a mutation on the round-up branch that the selected transactions do use (mulDivRoundingUp without its increment) is detected in 295, 298 and 299 of 300. " + mut_text()},
]

res = {"unit": "theme-producer-branch-coverage", "profiles": [], "findings": findings, "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(res, open(NR + '/cycles/024/theme-producer-branch-coverage.research.json', 'w'), indent=1)
print('written', len(findings), len(cleared))
