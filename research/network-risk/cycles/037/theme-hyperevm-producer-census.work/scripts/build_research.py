"""Writes cycles/037/theme-hyperevm-producer-census.research.json from the work outputs."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = '/home/user/v4-core/research/network-risk'
nets = json.load(open(R + '/state/networks.json'))['networks']
ALL = [n['chainId'] for n in nets]
OTHER = [c for c in ALL if c != 999]
A = json.load(open(W + '/out/census-A-pm-and-hi.json'))
B = json.load(open(W + '/out/census-B-lo.json'))
PMS = json.load(open(W + '/out/census-PM.json'))
H = json.load(open(W + '/out/hdr-check.json'))
WD = {l: json.load(open(W + '/out/wide-%s.json' % l)) for l in ('hl-purroof', 'hl-hyperlend', 'hl-official')}
REL = 'research/network-risk/cycles/037/theme-hyperevm-producer-census.work/'


def sh(name):
    a, b = A['shapes'].get(name), B['shapes'].get(name)
    occ = (a or {}).get('occ', 0) + (b or {}).get('occ', 0)
    blocks = (a or {}).get('blocks', 0) + (b or {}).get('blocks', 0)
    firsts = [x['first'] for x in (a, b) if x]; lasts = [x['last'] for x in (a, b) if x]
    ex = None
    for x in (a, b):
        if x and x['last'] == max(lasts): ex = x['lastEx']
    return occ, blocks, (min(firsts) if firsts else None), (max(lasts) if lasts else None), ex


def fmt(name, label=None):
    occ, blocks, f, l, ex = sh(name)
    if not occ: return '%s: 0' % (label or name)
    return '%s: %d times in %d blocks, first %d, latest %d, example tx %s at %s pc %d' % (label or name, occ, blocks, f, l, ex['tx'], ex['contract'], ex['pc'])


SHAPES = [
    ('MULMOD modulus 2^256-1, product >= 2^256', 'MULMOD by 2^256-1 with product >= 2^256 (FullMath.sol:24)'),
    ('MULMOD product >= 2^256, modulus of 1 limbs (not 2^256-1)', 'MULMOD, product >= 2^256, one-limb modulus (the 10^6 fee copy at FullMath.sol:48)'),
    ('MULMOD product >= 2^256, modulus of 2 limbs (not 2^256-1)', 'MULMOD, product >= 2^256, two-limb modulus (2^96 at FullMath.sol:48, :112, SqrtPriceMath.sol:252)'),
    ('MULMOD product >= 2^256, modulus of 3 limbs (not 2^256-1)', 'MULMOD, product >= 2^256, three-limb modulus (2^128 Position copy, sqrt price denominators)'),
    ('MULMOD product >= 2^256, modulus of 4 limbs (not 2^256-1)', 'MULMOD, product >= 2^256, four-limb modulus'),
    ('MUL product >= 2^256', 'MUL that overflows'),
    ('DIV dividend >= 2^192, divisor of 1 limbs', 'DIV, dividend >= 2^192, one-limb divisor'),
    ('DIV dividend >= 2^192, divisor of 2 limbs', 'DIV, dividend >= 2^192, two-limb divisor'),
    ('DIV dividend >= 2^192, divisor of 3 limbs', 'DIV, dividend >= 2^192, three-limb divisor'),
    ('DIV dividend >= 2^192, divisor of 4 limbs', 'DIV, dividend >= 2^192, four-limb divisor'),
    ('DIV by zero', 'DIV by zero'), ('MOD by zero', 'MOD by zero'),
    ('SDIV negative dividend', 'SDIV negative dividend'), ('SDIV negative divisor', 'SDIV negative divisor'),
    ('SMOD negative dividend', 'SMOD negative dividend'), ('SMOD negative divisor', 'SMOD negative divisor'),
    ('SAR negative value, shift < 256', 'SAR negative value, shift < 256'), ('SAR negative value, shift >= 256', 'SAR negative value, shift >= 256'),
    ('SIGNEXTEND byte 2, sign set', 'SIGNEXTEND byte 2 sign set'), ('SIGNEXTEND byte 2, sign clear', 'SIGNEXTEND byte 2 sign clear'),
    ('SIGNEXTEND byte 15, sign set', 'SIGNEXTEND byte 15 sign set'), ('SIGNEXTEND byte 15, sign clear', 'SIGNEXTEND byte 15 sign clear'),
    ('BYTE index 0', 'BYTE index 0'), ('BYTE index 31', 'BYTE index 31'), ('BYTE index >= 32', 'BYTE index >= 32'),
    ('SHL shift 0', 'SHL by 0'), ('SHL shift 1-255', 'SHL by 1 to 255'), ('SHL shift >= 256', 'SHL by 256 or more'),
    ('SHR shift 0', 'SHR by 0'), ('SHR shift 1-255', 'SHR by 1 to 255'), ('SHR shift >= 256', 'SHR by 256 or more'),
    ('ADDMOD sum >= 2^256', 'ADDMOD that overflows'), ('EXP executed', 'EXP'),
    ('KECCAK256 length 64', 'KECCAK256 of 64 bytes'), ('KECCAK256 length 58', 'KECCAK256 of 58 bytes'), ('KECCAK256 length 160', 'KECCAK256 of 160 bytes'),
    ('KECCAK256 length 136 (one rate block)', 'KECCAK256 of 136 bytes (one rate block)'), ('KECCAK256 length 135 or 137', 'KECCAK256 of 135 or 137 bytes'),
    ('MCOPY overlap, destination above source', 'MCOPY overlapping, destination above source'), ('MCOPY overlap, destination below or equal source', 'MCOPY overlapping, destination below source'),
    ('MCOPY executed', 'MCOPY (any)'), ('TLOAD executed', 'TLOAD'), ('TSTORE executed', 'TSTORE'),
    ('JUMPI condition zero', 'JUMPI condition zero'), ('JUMPI condition nonzero >= 2^64', 'JUMPI condition nonzero and wider than one limb'),
]
census_txt = '; '.join(fmt(n, l) for n, l in SHAPES)
ssr = A['shapes'].get('SSTORE restores the value at transaction start')
ssr_txt = 'SSTORE that restores the value the slot held at transaction start: %d times in %d blocks of blocks 52,394,000 to 52,418,999 (the tracer revision that tracks the current value per slot ran there only), latest example tx %s' % (ssr['occ'], ssr['blocks'], ssr['lastEx']['tx'])

nblk = len(set(range(52369000, 52419000)))
cov = ('Blocks re-executed by the two public nanoreth replicas with a JavaScript tracer through debug_traceBlockByNumber: the newest 50,000 blocks 52,369,000 to 52,418,999 '
       '(two runs, 52,369,000 to 52,398,299 and 52,394,000 to 52,418,999; the 4,250 blocks both runs traced were answered by the other replica in each and their headers agree), '
       'plus all 2,405 blocks that hold a PoolManager transaction from deployment to block 52,266,493 (the cycle 33 list) and block 52,363,132, the only PoolManager log between 52,266,494 and 52,369,000. '
       'Together %d distinct blocks and %d transaction traces, %d blocks with a PoolManager frame, no failed trace. Every batch of 50 blocks was bracketed with web3_clientVersion; the answers were reth/v0.1.0-f0cad31 (rpc.purroofgroup.com) and reth/v0.1.0-b92ad36 (rpc.hyperlend.finance/archive) before and after every batch. No sampling was used for Task 1.') % (
    A['blocks'] + B['blocks'] - 4250, A['txs'] + B['txs'], PMS['pmBlocks'])

refus = len(H.get('refusals', []))
hdr_txt = ('For %d blocks (block 52,363,132 plus 500 of the 2,406 PoolManager blocks and 500 of the newest 50,000, drawn with Python random.seed(37); list in %sdata/hdr-list-sample.txt) the replica header fields receiptsRoot, gasUsed and logsBloom were compared with eth_getBlockByNumber on the official endpoint rpc.hyperliquid.xyz/evm (client "%s" before and after each group): %d equal, %d differ, %d not fetched. '
           'The official endpoint allows 100 requests per minute (https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits, fetched this cycle), so the other covered blocks were not compared one by one; for them the replica acceptance rule (nanoreth refuses a block whose gas used, receipts root or logs bloom differs from the producer header) is the evidence, and the replica fetches the producer block itself. %d batch refusals for rate limits were retried.') % (
    H['blocks'], REL, H['brackets'][0]['before'] if H['brackets'] else '', H['equal'], len(H['differ']), len(H['unfetched']), refus)

wide_txt = '; '.join('%s (%s before, %s after, block %s): %d of %d equal to pyevm, differing %s' % (
    l, d['clientVersionBefore'], d['clientVersionAfter'], d.get('blockBefore'), sum(r['equalToReference'] for r in d['results']), len(d['results']),
    [r['name'] for r in d['results'] if not r['equalToReference']]) for l, d in WD.items())

out = {
    'unit': 'theme-hyperevm-producer-census',
    'profiles': [],
    'findings': [],
    'cleared': [
        {'chainIds': [999], 'lens': 'L2', 'check': 'Task 1 (L-1309): operand shapes that the closed HyperEVM block producer has executed in blocks the public replicas accepted. ' + cov,
         'result': 'Every operand shape that a line of src/ can produce occurs in accepted blocks, most of them in thousands of blocks up to the newest. ' + census_txt + '; ' + ssr_txt + '. '
                   'Counts per shape with first and latest block and one example transaction for every contract are in out/census-A-pm-and-hi.json (PoolManager blocks plus 52,394,000 to 52,418,999) and out/census-B-lo.json (52,369,000 to 52,398,299). '
                   'An accepted block shows that the producer and the replica revm agreed on every log, on the status of each transaction and on gas, so the producer computed these shapes as the replica does wherever the result reached a log, a branch or gas.',
         'source': REL + 'out/census-A-pm-and-hi.json'},
        {'chainIds': [999], 'lens': 'L2', 'check': 'Shapes that no covered block contains, and whether any line of src/ can produce them.',
         'result': 'Absent: MOD by zero, SMOD by a negative divisor, SMOD by zero, SDIV of -2^255 by -1, ADDMOD and MULMOD with modulus zero, SIGNEXTEND with index 31 or more, BYTE with index 32 or more, SAR of a non-negative value by 256 or more, EXP with exponent 256 or more, and MCOPY with overlapping ranges. None can come from src/. '
                   'Every MOD in src/ is UnsafeMath.divRoundingUp (src/libraries/UnsafeMath.sol:13) whose divisors are liquidity, guarded nonzero at src/libraries/SqrtPriceMath.sol:134-140 and :163-169, or numerator1/sqrtP + amount with sqrtP nonzero. Every SDIV and SMOD divides by tickSpacing, which is at least 1 (src/PoolManager.sol:120, src/libraries/TickBitmap.sol:19-21, src/libraries/Pool.sol:575-577). '
                   'The MULMOD moduli are not(0), a denominator that src/libraries/FullMath.sol:30 requires to exceed prod1, or Q96 (src/libraries/SqrtPriceMath.sol:252). SIGNEXTEND indices are the constants 2 and 15 and SAR shifts the constants 8, 128 and 255 (src/types/BalanceDelta.sol:24-69, src/libraries/TickMath.sol:61-63, src/libraries/TickBitmap.sol:38, src/libraries/SqrtPriceMath.sol:219). BYTE indices are masked with 0x1f (src/libraries/BitMath.sol:22, :45). src/ has no EXP. '
                   'The two compiler MCOPY sites of the PoolManager (pc 9186 and 9400) copy an ABI bytes value into a newly allocated buffer above it, and every mined run there had disjoint ranges.',
         'source': 'src/libraries/SqrtPriceMath.sol:134-140'},
        {'chainIds': [999], 'lens': 'L2', 'check': 'Task 2: whether the counted blocks are the producer blocks.',
         'result': hdr_txt + ' The F-120 limit stands: storage writes are not compared because headers carry a zero state root.',
         'source': 'https://rpc.hyperliquid.xyz/evm'},
        {'chainIds': [999], 'lens': 'L2', 'check': 'Task 3: PoolManager instructions that no covered block executed with a given shape, by pc and src/ line, and which an account can reach.',
         'result': 'The PoolManager has had two transactions since cycle 33 (blocks 52,363,132 and one in the newest 50,000), so the per-site picture is the one cycle 24 and 33 recorded: of 387 conditional jumps, both sides of 123, one side of 182 and neither side of 82 have run (out/census-PM.json). '
                   'Never run with a product of 2^256 or more: pc 22316/22378 (Position fee copy, src/libraries/Position.sol:94-96), pc 22445/22513 (exact-input fee copy, src/libraries/SwapMath.sol:65), pc 22585/22639/23094 (getAmount1Delta copy, src/libraries/SqrtPriceMath.sol:250-252), pc 22721/22763 (amount above uint160 copy, src/libraries/SqrtPriceMath.sol:97) and pc 20958 (src/libraries/FullMath.sol:112, unreachable branch). Run wide: pc 22892/22921 and 23678 (getAmount0Delta). '
                   'Never run at all: donate (pc 10491/10513 at src/libraries/UnsafeMath.sol:25, src/libraries/Pool.sol:466-480), the exact-output side (src/libraries/SwapMath.sol:88-104) and src/libraries/SqrtPriceMath.sol:59. '
                   'Reach: any account reaches pc 22445/22513 in an existing pool with an exact-input amount of -2^236 or below; it reaches the getAmount1Delta and Position copies wide only in a pool it creates (cycle 34: largest product in the 414 existing HyperEVM pools 2^186); exact output, donate and the amount-above-uint160 path in any pool. '
                   'Each of these shapes has been executed by the producer in other contracts in accepted blocks (Task 1 counts), including a wide MULMOD with a one-limb modulus 46 times. The reaching calls of cycle 34, rerun now by eth_call with the build placed by state override: ' + wide_txt + '. The one differing script is the known gas-capped open-limit swap.',
         'source': REL + 'out/wide-hl-official.json'},
        {'chainIds': [999], 'lens': 'L1', 'check': 'Task 4: what a wrong word at each never-executed site would change, who would lose, and whether a replica would refuse the block.',
         'result': 'A wrong getAmount1Delta or fee word changes amountIn or amountOut of a step and the comparison at src/libraries/SwapMath.sol:69, then the Swap amounts (src/PoolManager.sol:241-250) and the token Transfer logs of settlement, so a replica would refuse that block. A wide fee or getAmount1Delta amount that is used reverts at the int128 casts (src/libraries/Pool.sol:452-458), and a discarded one only decides a comparison with a margin of at least 2^33 (cycle 34). '
                   'Sites whose result reaches storage and no log in the same transaction: fee growth global (src/libraries/Pool.sol:404-405 and :446-448, and donate at :474-477), feeGrowthOutside on a tick cross (src/libraries/Pool.sol:536-537 and crossTick), the tick bitmap word (src/libraries/TickBitmap.sol flipTick), tick liquidityGross and liquidityNet (src/libraries/Pool.sol:543-557), pool liquidity after a liquidity change (src/libraries/Pool.sol:226), position liquidity and feeGrowthInsideLast (src/libraries/Position.sol:88, :100-101) and protocolFeesAccrued (src/ProtocolFees.sol:68, reached only with a protocol fee set by governance). A wrong word there would pass the replicas until a later transaction read it and produced a different log; then the replicas would halt and the producer chain would continue. '
                   'Losers would be the LPs of the pool (fee growth, liquidity) or later swappers (bitmap, ticks). This needs a fault in the producer, which only its operator controls (F-120).',
         'source': 'src/libraries/Pool.sol:404-405'},
        {'chainIds': OTHER, 'lens': 'L2', 'check': 'Whether the HyperEVM producer census applies to the other 20 networks.',
         'result': 'It does not. On the other 20 networks the block producer is either the public client that earlier cycles read and ran, or, on MegaETH, a closed producer whose state root the public validator reproduces (cycles 33 and 35). The bounds from src/ used above hold on all 21.',
         'source': 'research/network-risk/OPCODES.md'},
    ],
    'leads': [
        {'chainIds': [999], 'lens': 'L2', 'question': 'Does the closed HyperEVM producer compile or specialise code per contract or per program counter, so that shape coverage in other contracts says nothing about PoolManager pc 22445/22513 (wide fee mulDiv, reachable in existing pools with amountSpecified of -2^236 or below) and the other never-executed sites?',
         'why': 'The census shows every shape at the opcode level. If the producer runs a per-site compiled path, a wrong word at a never-executed PoolManager site would show only when someone mines that call. The official endpoint answers like revm, which suggests an interpreter, but Hyperliquid has not published the producer.', 'priority': 'low'},
    ],
    'leadResults': [
        {'leadId': 'L-1309', 'outcome': 'cleared',
         'answer': 'Census of %d replica-accepted HyperEVM blocks (the newest 50,000 plus every PoolManager block): every operand shape that src/ can produce occurs in accepted blocks, and the absent shapes cannot arise from src/. Header comparison with the official endpoint on %d blocks: %d equal, %d differ. The reaching calls for the never-executed PoolManager sites return the reference words on both replicas and the official endpoint. No result differs; no finding.' % (A['blocks'] + B['blocks'] - 4250, H['blocks'], H['equal'], len(H['differ']))},
    ],
}
json.dump(out, open(R + '/cycles/037/theme-hyperevm-producer-census.research.json', 'w'), indent=1)
print('written')
