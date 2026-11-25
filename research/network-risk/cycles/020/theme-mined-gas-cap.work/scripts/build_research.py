import json
W = 'research/network-risk/cycles/020/theme-mined-gas-cap.work/out/'
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
OP7 = [10, 8453, 130, 7777777, 480, 57073, 1868]

cleared = []
def C(ids, lens, check, result, source):
    cleared.append({'chainIds': ids, 'lens': lens, 'check': check, 'result': result, 'source': source})

C(ALL, 'L3',
  'Lead L-913, measured. For each network, the gas cap of a mined ordinary transaction, and the gas of a full liquidity exit of a real position by its real owner at the real PoolManager, compared with that cap and not with the eth_call limit.',
  'Every sampled exit fits under the mined cap with a margin of at least 15 times on every network, including HyperEVM small blocks. Method: for each network, positions of the deployed PositionManager were sampled below nextTokenId (the newest 40 ids and random older ones), kept when liquidity > 0 and hooks = 0, and eth_estimateGas was called from ownerOf(tokenId) for modifyLiquidities with BURN_POSITION (all liquidity removed and fees collected) then TAKE_PAIR to the owner, on 2026-11-25. Largest estimate per network (positions estimated): Ethereum 232,219 (20), OP Mainnet 281,366 (9), Base 235,285 (20), Unichain 234,404 (7), Zora 222,099 (20), World Chain 285,481 (20), Ink 167,714 (4), Soneium 240,197 (20), Celo 243,990 (20), X Layer 215,639 (20), Arbitrum One 258,999 (20), Robinhood Chain 269,856 (20), Elysium 223,274 (20), Polygon 403,097 (20), BNB Chain 320,073 (19), Avalanche 264,918 (20), Monad 382,525 (18), MegaETH 534,813 (20), Tempo 976,067 (20), Arc 205,841 (20), HyperEVM 197,982 (20). Mined caps: 16,777,216 on Ethereum, the seven OP Stack chains, BNB Chain and Arc; 30,000,000 on Celo (block limit), Monad and Tempo; 32,000,000 on the Arbitrum family; 33,554,432 on Polygon; 3,000,000 in HyperEVM small blocks and 30,000,000 in big blocks; at least 50,000,000 on Avalanche and 210,000,000 on X Layer (block limit); at least 984,000,000 on MegaETH (mined user transactions). The worst ratio is Tempo, 976,067 against 30,000,000. The two failures (one burned between calls on OP Mainnet, one BNB Chain token whose transfer reverts, 0x9c3aba46) are not gas. The gas of the exit does not grow with anything another account does: Pool.modifyLiquidity has no loop (src/libraries/Pool.sol:146-238), it writes two tick words, at most two bitmap words, the position (src/libraries/Position.sol:76-101) and the pool liquidity (Pool.sol:226), and clears ticks with delete (Pool.sol:592-594). The only zero to nonzero writes it can make are the two fee growth inside words of the position (Position.sol:100-101), which depend on the position, not on others. Outputs: out/exits.json, out/exits_137.json.',
  'research/network-risk/cycles/020/theme-mined-gas-cap.work/out/exits.json; src/libraries/Pool.sol:146-238; src/libraries/Position.sol:76-101; https://eips.ethereum.org/EIPS/eip-7825')

C(ALL, 'L3',
  'Claim redemption under the mined cap: burn(holder, id, balance) and take(currency, holder, balance) by real ERC-6909 holders at the real PoolManager, run with a gas limit of 16,777,216 (3,000,000 on HyperEVM).',
  'Fits by a wide margin where measured. A measuring driver placed by state override at each holder address called unlock and, in the callback, burn and take, recording GAS around each call, then reverted. 14 networks returned holders from recent Transfer logs: Ethereum 8 of 8 succeeded, largest burn plus take 56,374 gas; OP Mainnet 38,236; Unichain 55,336; World Chain 38,236; Ink 58,548; Celo 7 of 7, 38,839; X Layer 55,342; Arbitrum One 6 of 8, 58,815 (two token transfers reverted inside take, a token property); Robinhood Chain 134,721; Elysium 54,733; Polygon 78,557; Avalanche 4 of 4, 44,689; Monad 105,405; Arc 44,461. Base, Zora, Soneium, BNB Chain, MegaETH, Tempo and HyperEVM returned no holder (rate limits or no Transfer logs in the window). The code path has no loop on any network: burn is one tstore delta and one balance write, plus one allowance write when the caller is not the owner (src/PoolManager.sol:332-336, src/ERC6909Claims.sol:13-22, src/ERC6909.sol:85), and take is one delta and one transfer (src/PoolManager.sol:291-297). Output: out/claims.json.',
  'research/network-risk/cycles/020/theme-mined-gas-cap.work/out/claims.json; src/PoolManager.sol:291-297; src/PoolManager.sol:332-336; src/ERC6909Claims.sol:13-22')

C(ALL, 'L3',
  'Do public endpoints apply the mined cap to simulation? eth_call with gas 16,777,216, 16,777,217, 30,000,000, 30,000,001, 33,554,433 and 60,000,000 to an address without code, and a binary search of the largest gas need for which eth_estimateGas still succeeds (probe contract by state override that reverts unless GAS is at least X).',
  'eth_call accepted 60,000,000 gas on all 21 endpoints, so no eth_call result says anything about the mined cap. eth_estimateGas does apply a ceiling: it returned at most 16,777,216 on Ethereum (reth v2.11.0), the seven OP Stack chains, BNB Chain and Arc; 30,000,000 on Celo, Tempo and HyperEVM; about 32,000,000 of execution gas on Arbitrum One, Robinhood Chain and Elysium; 33,554,432 on Polygon; 50,000,000 on Avalanche; 150,000,000 on Monad; 210,000,000 on X Layer; and no ceiling below 2^32 on MegaETH. On Monad the estimator ceiling is the block limit, above the 30,000,000 per transaction limit that consensus enforces, so an estimate on Monad can exceed what can be mined. No exit needs more than 1,000,000 gas, so the mismatch does not reach the PoolManager.',
  'research/network-risk/cycles/020/theme-mined-gas-cap.work/out/probe_caps.json; research/network-risk/cycles/020/theme-mined-gas-cap.work/out/estcap.json; https://docs.monad.xyz/developer-essentials/gas-pricing')

C(OP7 + [1, 56, 5042], 'L3', 'Source of the 16,777,216 cap on Ethereum, the OP Stack chains, BNB Chain and Arc.',
  'EIP-7825 rejects any transaction with a gas limit above 2^24 at txpool and block validation. Karst (Upgrade 19) activates it on OP Mainnet, Soneium, Ink, Unichain and Zora, with deposits exempt. BEP-652 makes it mandatory on BNB Chain; the largest user transaction in 300 recent BNB Chain blocks (135,712,831 to 135,713,130) had exactly 16,777,216 gas, and the larger ones are zero-price system transactions to 0x1000. On Base, World Chain and Arc the estimator ceiling of exactly 16,777,216 is the evidence; this closes lead L-110 for Arc and the cap part of L-095 for World Chain.',
  'https://eips.ethereum.org/EIPS/eip-7825; https://docs.optimism.io/notices/upgrade-19; https://raw.githubusercontent.com/bnb-chain/BEPs/master/BEPs/BEP-652.md; research/network-risk/cycles/020/theme-mined-gas-cap.work/out/scan_user_4326_56.json')

C([42161, 4663, 99901], 'L3', 'Mined cap on the Arbitrum family, read from ArbGasInfo.',
  'getGasAccountingParams() at 0x6c returns speedLimit 7,000,000, gasPoolMax 32,000,000 and maxTxGasLimit 32,000,000 on all three chains. A mined Arbitrum One transaction (0x4d2011c4...e988) carried 32,003,281 gas including the parent chain data component. Exits use at most 270,000.',
  'eth_call 0x612af178 to 0x000000000000000000000000000000000000006C on arb1.arbitrum.io, rpc.mainnet.chain.robinhood.com and rpc.elysium.kinetiq.xyz, output research/network-risk/cycles/020/theme-mined-gas-cap.work/out/arbgasinfo.txt')

C([143, 4217], 'L3', 'Mined caps on Monad and Tempo.',
  'Monad documents a 30M transaction gas limit and a 150M block limit; consensus (TfmValidator, TFM_MAX_GAS_LIMIT) rejects larger transactions. Tempo TIP-1010 caps a transaction at 30,000,000 and general (non-payment) gas at 30,000,000 per block. Tempo exits, the costliest measured because a new storage slot costs 250,000 gas, use at most 976,067. A removal can add at most two fresh writes beyond what was sampled (Position.sol:100-101), about 500,000 more on Tempo.',
  'https://docs.monad.xyz/developer-essentials/gas-pricing; https://d3qv7503rlaw88.cloudfront.net/uploads/Monad_Execution_Report_e1563cbb25.pdf; https://github.com/tempoxyz/tempo/blob/main/tips/tip-1010.md')

C([999], 'L3', 'HyperEVM: does an exit fit a small block, which every account uses unless it sets the big block flag on HyperCore?',
  'Yes. Small blocks hold 3,000,000 gas and big blocks 30,000,000. The largest sampled exit used 197,982 gas, so 15 such exits fit one small block. The estimator ceiling of 30,000,000 is the big block size, so an estimate between 3,000,000 and 30,000,000 is only minable after the flag is set.',
  'https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/dual-block-architecture; research/network-risk/cycles/020/theme-mined-gas-cap.work/out/exits.json')

C([4326], 'L3', 'MegaETH, normal sequencer path: can an ordinary account grow the SALT bucket of a victim position\'s fee growth words until the two fresh writes of a removal (Position.sol:100-101) exceed what one user transaction can carry?',
  'Not at a practical cost. User transactions with 984,000,000 gas were mined in blocks 32,838,613 to 32,838,912, so the per transaction cap set by the sequencer is at least that. Under the rule recorded in F-105 (storage gas 20,000 times (multiplier minus 1), a bucket doubles at 80 percent use), two writes exceed 984,000,000 only at multiplier 32,768. My model puts that at about 3.36 million entries in one bucket and 7.3e14 gas, about 733 ETH at the 1,000,000 wei base fee floor, spread over about 74,000 blocks, because each entry costs more as the bucket grows and a 10,000,000,000 gas block holds fewer of them. The base fee would rise long before that. The L1 deposit path with its 1,000,000 gas limit stays F-105.',
  'https://docs.megaeth.com/spec/megaevm/resource-limits.md; research/network-risk/cycles/020/theme-mined-gas-cap.work/out/scan_user_4326_56.json')

C([42220, 196, 43114], 'L3', 'Celo, X Layer and Avalanche, where no 2^24 cap is active.',
  'The estimator accepted gas up to the block limit on Celo (30,000,000) and X Layer (210,000,000), and up to 50,000,000 on Avalanche (block limit 80,000,000). The largest user transactions in 120 recent blocks were 9,000,000 (Celo), 10,000,000 (X Layer) and 5,943,301 (Avalanche). Exits use at most 265,000.',
  'research/network-risk/cycles/020/theme-mined-gas-cap.work/out/estcap.json; research/network-risk/cycles/020/theme-mined-gas-cap.work/out/scan_user_more.json')

C([137, 143, 4217] + OP7, 'L3', 'Scripts in OPCODES.md that ran out of gas or ran above the mined cap under eth_call (full-range swaps on Polygon, Monad and Tempo, scripts above 16,777,216 on the OP Stack chains).',
  'These are swaps. Pool.swap stops at the caller\'s sqrtPriceLimitX96 (src/libraries/Pool.sol:344), so a swap too long for one transaction is split by price limits, and no victim needs a swap to exit. The dust-tick cost hazard is already F-064, F-111, F-115, F-039 and F-063.',
  'src/libraries/Pool.sol:344')

leads = [
    {'chainIds': [4326], 'lens': 'L3', 'question': 'What per transaction gas cap does the MegaETH sequencer apply to user transactions? Mined user transactions show at least 984,000,000 and the estimator has no ceiling below 2^32.',
     'why': 'The SALT growth cost bound for removals above uses the mined lower bound. A much lower configured cap would lower the cost of closing a removal on the normal path.', 'priority': 'low'},
    {'chainIds': [8453, 7777777, 1868, 56, 4326, 4217, 999], 'lens': 'L3', 'question': 'Rerun claims.py (burn and take by real ERC-6909 holders under the mined cap) on Base, Zora, Soneium, BNB Chain, MegaETH, Tempo and HyperEVM through endpoints that serve eth_getLogs without rate limits.',
     'why': 'The path has no loop, but these seven networks have no measured redemption, and Tempo prices fresh slots at 250,000 gas.', 'priority': 'low'},
]
leadResults = [
    {'leadId': 'L-913', 'outcome': 'cleared', 'answer': 'All 21 networks: the largest sampled full exit (BURN_POSITION plus TAKE_PAIR by the real owner) used 197,982 to 976,067 gas, and the smallest mined cap is 3,000,000 (HyperEVM small block); elsewhere at least 16,777,216. The exit has no loop. Claim burn and take used at most 134,721 gas on the 14 networks measured.'},
    {'leadId': 'L-110', 'outcome': 'cleared', 'answer': 'Arc\'s eth_estimateGas ceiling is exactly 16,777,216, and an estimate needing 16,756,212 gas of execution fails, so the node enforces the EIP-7825 cap. Exits use at most 205,841.'},
]
out = {'unit': 'theme-mined-gas-cap', 'profiles': [], 'findings': [], 'cleared': cleared, 'leads': leads, 'leadResults': leadResults}
json.dump(out, open('research/network-risk/cycles/020/theme-mined-gas-cap.research.json', 'w'), indent=1)
