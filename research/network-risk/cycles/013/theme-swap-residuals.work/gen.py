"""Builds ../theme-swap-residuals.research.json from totals.json, raw/inblock.json and raw/r2-*.json."""
import json
from endpoints import NETS
T = json.load(open('totals.json')); IB = json.load(open('raw/inblock.json'))
tot = T['totals']; ALL = [n for n in NETS]
W = 'research/network-risk/cycles/013/theme-swap-residuals.work'
cleared = []
for o in T['networks']:
    cid = o['chainId']; d = json.load(open(f'raw/r2-{cid}.json')); ib = IB[str(cid)]
    z = o['zeroAmount']; zn = sum(z.values()) if z else 0
    k = o['fullLoopKey'] or {}
    txt = (f"{o['name']}: {o['swaps']} Swap events of the PoolManager in blocks {o['blocks'][0]} to {o['blocks'][1]}. "
           f"All pass the tick relation ({o['tick']['boundary']} on a lower tick boundary). {o['singleStep']} match a single step of SwapMath.computeSwapStep to the unit "
           f"and the other {o['fullLoop']} match the full Pool.swap loop to the unit in price, tick, liquidity and both amounts, the longest with {o['maxSteps']} steps"
           + (f"; {k.get('known', 0)} of them with the pool key read on chain and {k.get('spacingInferred', 0)} with a tick spacing found by trial" if k else '')
           + (f"; {zn} of them are zero-amount swaps that leave the pool unchanged" if zn else '') + ". "
           f"{ib['afterEarlierEventSameBlock']} swaps followed an earlier event of the same pool in the same block and were rerun from the state carried forward by log index, "
           f"{ib['afterModifySameBlock']} of them after a liquidity change in that block. None was set aside and none is unmatched. ")
    if o['feeCheck']['static']:
        txt += f"For {o['feeCheck']['static']} full-loop swaps on static-fee pools the event fee equals the fee slot0 gives (lpFee, or calculateSwapFee with the protocol fee), with no mismatch. "
    if o['feeGrowth']['checked']:
        txt += f"For {o['feeGrowth']['checked']} full-loop swaps alone in their block the change of feeGrowthGlobal in storage equals the sum of the per-step fees after the protocol share, divided by liquidity, with {o['feeGrowth']['checked'] - o['feeGrowth']['match']} mismatches. "
    sm = o['storedSamples']
    if sm['n']:
        txt += f"{sm['replayed']} of the {sm['n']} multi-step and unmatched samples stored by cycles 8 to 12 for this network replay to the unit (longest {sm['maxSteps']} steps)."
    cleared.append({'chainIds': [cid], 'lens': 'L1', 'check': f"Mined swaps on {o['name']} rerun from exact state with replay2.py: single-step formulas, then the whole swap loop with the real pool key, tick bitmap and liquidityNet",
                    'result': txt.strip(), 'source': f"eth_getLogs and eth_call extsload(bytes32[]) at the parent block on {', '.join(d['logUrls'][:1] + d['stateUrls'][:1])}; output {W}/raw/r2-{cid}.json"})

cleared += [
    {'chainIds': ALL, 'lens': 'L1', 'check': 'The stored residue of earlier cycles: every multiSamples and otherSamples entry of the swaps*.json files of cycles 8 to 12 and of opcodes/swaps.json and opcodes/swaps-deep.json, rerun with the pool key and the in-block liquidity changes',
     'result': f"{tot['samplesReplayed']} of {tot['samples']} distinct stored samples replay to the unit. They include the cases earlier replays left open: 22 distinct Arbitrum One swaps and 33 Avalanche swaps whose state the endpoint did not serve then, the Robinhood Chain swap 0xa09408584e59830bd1b52f61708e4ff3e22cff374da4483b3e64e76e8e7094c9 (2 steps, spacing 10), and the four Ink swaps at spacing 90. 24 BNB Smart Chain samples first came back as 'swap log not found' because bsc-rpc.publicnode.com returned an empty log list for block 135442034, where bsc.rpc.sentio.xyz returns the two logs; with that endpoint all 52 BNB samples replay.",
     'source': f"{W}/raw/samples.json and {W}/raw/samples-56.json (samples.py)"},
    {'chainIds': ALL, 'lens': 'L1', 'check': 'Swap events with amount0 = amount1 = 0 and price, tick and liquidity unchanged, which the step formulas cannot produce',
     'result': f"{tot['zeroAmount']} such events across the windows. PoolManager.swap rejects amountSpecified == 0 (src/PoolManager.sol:193), and a nonzero amount always moves the price or spends the amount (src/libraries/Pool.sol:344-437, src/libraries/SwapMath.sol:63-105). The only path to a zero swap is a hook with BEFORE_SWAP_RETURNS_DELTA_FLAG whose specified delta cancels the amount (src/libraries/Hooks.sol:266-277), after which Pool.swap returns ZERO_DELTA without touching state (src/libraries/Pool.sol:320). Every such event whose pool key was found has a hook address with bit 3 set; the rest are on pools whose key no public source gave, and they fit only that path. The event is correct and moves no funds.",
     'source': 'src/libraries/Hooks.sol:266-277'},
    {'chainIds': ALL, 'lens': 'L1', 'check': 'Pools initialized inside the window, where the parent block has an empty slot0',
     'result': f"{sum(o['initInWindow'] for o in T['networks'])} pools were initialized inside the windows. In a first run that started from the zero slot0 of the parent block, the first swaps of such pools came out unmatched on Ethereum and Zora. Started from the Initialize event (sqrtPriceX96 and tick, lpFee from the key, src/PoolManager.sol:128-138, src/libraries/Pool.sol:100-107) and carried through the liquidity added in the same block, all match. The protocol fee of a new pool is zero in this build: initialize sets no protocol fee (src/libraries/Pool.sol:105-106).",
     'source': 'src/libraries/Pool.sol:100-107'},
    {'chainIds': ALL, 'lens': 'L1', 'check': 'Event semantics for pools with hooks that return deltas: the Swap event carries the pool delta of Pool.swap, computed from amountToSwap after the beforeSwap delta, before afterSwap adjusts the caller delta',
     'result': 'src/PoolManager.sol:202-250 emits delta.amount0(), delta.amount1() of pool.swap(params) with amountSpecified = amountToSwap, so a hook delta changes the specified amount the loop starts from and never the arithmetic the event reports. The replay therefore needs no special case for return-delta hooks: it derives the specified amount from the event, and all swaps on return-delta hook pools in the windows match. Hook and token behaviour was not swept (owner instruction).',
     'source': 'src/PoolManager.sol:230-250'},
]
leadResults = [{'leadId': 'L-679', 'outcome': 'cleared', 'answer': (
    f"Closed. Fresh windows on all 21 networks give {tot['swaps']} mined swaps: {tot['singleStep']} match one step of computeSwapStep and the other {tot['fullLoop']} match the full Pool.swap loop to the unit in amount0, amount1, sqrtPriceX96, liquidity and tick, with the event fee checked against slot0 on {tot['feeStatic']} swaps of static-fee pools and the feeGrowthGlobal change in storage checked on {tot['feeGrowthChecked']} swaps. None is set aside and none is unmatched. "
    f"The {tot['samples']} distinct samples stored by cycles 8 to 12 all replay as well, including those earlier endpoints could not serve. The residue of about 3,300 pairs in OPCODES.md is swaps that take several steps or cross initialized ticks. Rerun with the real pool key they all match, including pools whose tick spacing the old candidate list lacked (90 on Ink, 190 on Arc). The new windows add two kinds the single-step test cannot take: pools initialized inside the window and zero-amount swaps of return-delta hooks; both match as well. "
    "No line of SwapMath, SqrtPriceMath, FullMath, TickMath, TickBitmap, LiquidityMath, UnsafeMath or Pool computes anything other than the source says on any network's mined blocks. replay2.py sits in the unit's work directory because this cycle may not write to tools/opdiff.")}]
leads = [
    {'chainIds': [42220, 480], 'lens': 'L1', 'question': f"Celo and Worldchain windows hold fewer than 3,000 swaps (Celo {next(o['swaps'] for o in T['networks'] if o['chainId'] == 42220)}, Worldchain {next(o['swaps'] for o in T['networks'] if o['chainId'] == 480)}) because the collection budget ran out; a longer collection with replay2.py would extend the mined-swap evidence there.",
     'why': 'More mined swaps on the two thinnest windows; the result so far has no mismatch.', 'priority': 'low'},
]
out = {'unit': 'theme-swap-residuals', 'profiles': [], 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(out, open('../theme-swap-residuals.research.json', 'w'), indent=1)
print('written', len(cleared), 'cleared')
