"""Writes cycle 34 theme-reth-journal-and-execution-cache.research.json from the reads and runs of this work dir."""
import json, os

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(W, '..', 'theme-reth-journal-and-execution-cache.research.json')
S = json.load(open(os.path.join(W, 'out', 'slotcmp', '1.json')))  # noqa: F841  (presence check)

RETH = 'https://raw.githubusercontent.com/paradigmxyz/reth/v2.11.0/'
OP260 = 'https://raw.githubusercontent.com/ethereum-optimism/reth/3c5f2f11c4e5a5647e6e911cd131ccf1bada4f25/'
OP270 = 'https://raw.githubusercontent.com/ethereum-optimism/reth/ce8cfb1fd25c2da86004eda677dc55dfa0d5c0af/'
BASE = 'https://raw.githubusercontent.com/base/reth/9e380dd9b22f95649fb1b5e84c85449ef03f5dca/'
OKX = 'https://raw.githubusercontent.com/okx/reth/81573d2c7d806d5df9ff2d512dd000c2bf542b1b/'
R230 = 'https://raw.githubusercontent.com/paradigmxyz/reth/v2.3.0/'
CELO = 'https://raw.githubusercontent.com/celo-org/reth/74cc8bbce7631c3586ab446460590fef6630d258/'
CS = 'crates/engine/execution-cache/src/cached_state.rs'
LIB = 'crates/engine/execution-cache/src/lib.rs'
PW = 'crates/engine/tree/src/tree/payload_processor/prewarm.rs'
MOD = 'crates/engine/tree/src/tree/payload_processor/mod.rs'
PV = 'crates/engine/tree/src/tree/payload_validator.rs'

RETH_CHAINS = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 4326, 5042]
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]

cleared = []


def c(ids, lens, check, result, source):
    cleared.append({'chainIds': ids, 'lens': lens, 'check': check, 'result': result, 'source': source})


c([1], 'L2',
  'Task 2 at reth v2.11.0 (the Ethereum endpoint answered reth/v2.11.0-b9abbcc on 2026-11-27): the key of each execution cache entry and where every cached value comes from.',
  'Code is keyed by the full 32 byte code hash, storage by the full (Address, StorageKey) pair and accounts by the full address (cached_state.rs lines 963-971), in fixed-cache tables that compare the stored key before returning a value, as cycle 32 recorded. Values enter the cache in three ways only. insert_state writes the final present_value of every slot and the final info of every modified account of an executed block (lines 1133-1206). get_or_try_insert_*_with inserts, on a miss, the value the underlying state provider returns, and only providers built with CacheFillMode::FillOnMiss do that (lines 276-278, 846-941); block execution uses LookupOnly except on the paths payload_validator.rs lines 650-690 name. clear() empties storage and accounts and keeps code, whose hash mapping cannot change (lines 1213-1219). No path inserts a value that a transaction wrote and later reverted, because a speculative execution keeps its writes in its own EVM state and the provider underneath only sees reads.',
  RETH + CS)

c([1], 'L2',
  'Task 2 at reth v2.11.0: when the cross-block cache is kept, replaced or dropped after a block.',
  'save_cache runs only after every prewarm worker has finished and the Terminate event carries the block output (prewarm.rs lines 653-715). Under the mutex it applies insert_state of the executed block to the checked out cache, waits for the validity signal, and on an insert error or an invalid block takes the stored cache out, so nothing is kept (prewarm.rs lines 468-517). get_cache_for hands a cache out only when no other handle exists and clears it with clear_with_hash when its block hash is not the parent of the new block (lib.rs lines 59-105); a cache still held elsewhere is not reused and a fresh empty one is built (mod.rs lines 501-514). Locally built blocks go through on_inserted_executed_block, which skips the update when the stored hash is not the parent or the cache is in use (mod.rs lines 523-566). A later block therefore starts from either the post-state of its exact parent or an empty cache.',
  RETH + PW)

c([1], 'L2',
  'Task 2 at reth v2.11.0: insert_state for an account created and destroyed in one transaction (EIP-6780), a slot written back to zero, and an account whose code changed through EIP-7702 delegation.',
  'A destroyed account whose original info had code clears the whole storage and account cache and returns (cached_state.rs lines 1165-1182); a destroyed account without original code and with no current info is removed from the account cache, and one re-created in the block has its new storage and info written (lines 1183-1203). A slot whose final value is zero is inserted as zero (insert_storage, line 1100) and read back through nonzero_storage_value as absent, which the EVM reads as zero (lines 841-843, 877-910). A delegation changes the account code hash, which insert_account replaces, and the designator bytecode is looked up by its own hash; a code hash missing from the cache goes to the provider. None of these leaves a word that differs from the post-block state. The PoolManager has code and cannot be destroyed, so only the plain write path ever touches its slots.',
  RETH + CS)

c([1], 'L2',
  'Task 2 at reth v2.11.0: can a prewarm result, a txpool snapshot or a block access list prefetch put a word into the cache that the state does not hold?',
  'No on any path. Prewarm workers wrap the provider in new_prewarm (FillOnMiss) and insert only what the parent state provider returns (prewarm.rs lines 800-806, 920-928); their EVM writes stay in the worker. The txpool snapshot is a copy of CachedReads, which records only values the inner provider returned (crates/evm/evm/src/cached.rs lines 100-155), is built over the head the worker was started for, and is served only to a block whose parent hash equals it (tree/txpool_prewarm/control.rs lines 50-56). The block access list prefetch takes only the addresses and slot keys from the list and reads their values from the parent state provider (prewarm.rs lines 604-631, bal_prewarm_pool.rs lines 159-199); end_block waits until every worker has drained its queue and dropped its provider before the cache is saved (bal_prewarm_pool.rs lines 108-122). Txpool prewarming and result reuse are off by default (engine primitives config.rs lines 263-286; node args engine.rs lines 392-397, 572-577), and no listed network has block access lists active. A speculative result is reused only after every recorded storage read matches and every account read matches or is rebased on balance alone (reuse.rs lines 223-348), as cycle 31 recorded.',
  RETH + PW)

c([10, 130, 57073, 1868, 7777777, 480], 'L2',
  'Task 2 at the ethereum-optimism/reth revisions behind the OP Stack endpoints: op-v2.6.0-2 (3c5f2f1; op-reth v2.8.1, conduit-op-reth v2.5.1, world-chain v2.8.2) and op-v2.7.0-2 (ce8cfb1; op-reth v2.10.0-rc.4).',
  'op-v2.7.0-2 cached_state.rs differs from reth v2.11.0 only in two import lines and a test import, so every rule above holds line for line (insert_state 1133-1206, storage cache 968). op-v2.6.0-2 has the same fill modes (new_prewarm at line 141, FillOnMiss only on the paths of payload_validator.rs line 684), the same save_cache under the mutex with the cache taken out on an insert error or an invalid block (prewarm.rs lines 289-335), the same fork clear in get_cache_for (lib.rs lines 59-97), and the older destroyed-account branch at cached_state.rs lines 1286-1305 that F-133 records; that branch cannot reach an address with code.',
  OP260 + PW)

c([8453], 'L2',
  'Task 2 at base/reth 9e380dd (Base v1.5.6, which mainnet.base.org and base-rpc.publicnode.com both reported on 2026-11-27).',
  'Same keys and fill modes as above (cached_state.rs storage cache line 1082, insert_state 1247-1330 with the older destroyed-account branch at 1278-1297; payload_validator.rs line 673 sets FillOnMiss only on the listed paths). save_cache inserts the block output under the mutex and sets the stored cache to None on an insert error or an invalid block (prewarm.rs lines 282-330). Fork blocks clear the cache (lib.rs lines 59-97). No path stores a word that differs from the post-state of an address with code.',
  BASE + PW)

c([196, 4326, 42220], 'L2',
  'Task 2 at okx/reth 81573d2 (X Layer v0.0.7), reth v2.3.0 (the base mega-reth v2.3.1 is assumed to build on; mega-reth itself is not public) and celo-org/reth 74cc8bb (Celo).',
  'okx/reth 81573d2 cached_state.rs is byte identical to reth v2.3.0. In both, insert_state (lines 873-950) writes present values and has the older destroyed-account branch at 904-923; providers fill on miss only on the prewarm paths (payload_validator.rs lines 541-556); save_cache sets the stored cache to None on an insert error and on an invalid block (prewarm.rs lines 273-322); get_cache_for clears on a parent mismatch (lib.rs lines 56-94). Celo 74cc8bb selects the fill rule with a const generic PREWARM instead of a mode (cached_state.rs lines 110-131, 466-500) with the same effect, and its save_cache is the same as v2.3.0 (prewarm.rs lines 273-322). Which reth revision mega-reth v2.3.1 pins could not be confirmed.',
  OKX + CS)

c([1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 4326, 5042, 4217], 'L2',
  'Task 3: on one endpoint per reth-derived network, eth_getStorageAt against extsload(bytes32[]) through eth_call for PoolManager slots written in the newest blocks, at the writing block B and at B+1, against a second provider at B, and against the sqrtPriceX96, tick and liquidity of the last Swap event of each pool in B. Each batch was bracketed by web3_clientVersion (work/out/slotcmp/*.json).',
  'No difference on 2,477 slots. Per network (slots, builds answering primary and second): Ethereum 200 (reth v2.11.0-b9abbcc; blastapi reth v2.10.0-f5192ac), OP Mainnet 200 (op-reth v2.8.1-72207294; publicnode op-reth v0.0.0-dev), Base 200 (base v1.5.6 on publicnode as primary because mainnet.base.org answered eth_getLogs with HTTP 429; mainnet.base.org as second), Unichain 200, Ink 200 and Soneium 143 (op-reth v2.10.0-rc.4-65e80332), Zora 200 (conduit-op-reth v2.5.1-8f0ccac), World Chain 200 (world-chain v2.8.2-9596311; worldchain.drpc.org returned HTTP 500 so no second comparison), Celo 179 (reth v2.2.0-74cc8bb), X Layer 200 (xlayer v0.0.7 on both), MegaETH 155 (mega-reth v2.3.1-4499c42), Arc 200 (arc/v1), Tempo 200 (tempo v1.19.2-c0c9372). drpc second providers report a generic Geth/v10.0.0/drpc and their build is unknown. 1rpc.io refused with a usage limit, soneium-rpc.publicnode.com and celo-rpc.publicnode.com with HTTP 403, xlayer.drpc.org with a rate limit. 248 event checks of slot0 and liquidity matched. The slots are slot0, both fee growth words, liquidity, the three words of every tick in the events, three position words per ModifyLiquidity and one bitmap word at tick >> 8 without compression by tick spacing, so some bitmap and swap tick slots are words the block did not write; 728 of the 2,477 values are nonzero. No difference persisted across blocks and no lag between providers was seen.',
  'eth_getStorageAt and eth_call extsload(bytes32[]) on the 13 endpoints listed, 2026-11-27; scripts/slotcmp.py')

c([480], 'L2',
  'Task 4, source part: the execution stack of world-chain v2.8.2 (9596311, the build the World Chain endpoint answers) against op-reth v2.8.1 and v2.10.0-rc.4.',
  'The node crates (reth-evm, reth-revm, reth-engine-tree, reth-optimism-evm, op-revm and alloy-op-evm at optimism rev 7220729) depend on revm 43.0.3 with revm-interpreter 43.0.2, the stack of op-reth v2.10.0-rc.4; the revm 42.0.1 stack in the lock is used only by kona proof crates at optimism rev da6d325. ruint 1.20.0, fixed-cache 0.1.10 and reth-execution-cache at op-v2.6.0-2 are the same as op-reth v2.8.1. alloy-primitives is 1.6.1 and keccak-asm and sha3-asm are 0.1.8, against 1.7.3 and 0.1.6 in op-reth. The two sha3-asm crates (checksums a6287fd6... and 59cbb88c..., equal to the lock entries) select the same perlasm file for a default linux build, keccak1600-x86_64.pl on x86-64 and keccak1600-armv8.pl on aarch64, and both files and x86_64-xlate.pl are byte identical; 0.1.8 changes symbol naming, the Apple-only SHA3 extension rule, a Zen 5 rule and patch matching. The binary itself was not fetched or compared in this cycle.',
  'https://raw.githubusercontent.com/worldcoin/world-chain/v2.8.2/Cargo.lock')

c([42161, 4663, 99901, 137, 56, 43114, 143, 999], 'L2',
  'Whether this theme applies to the networks that do not run a reth-derived client for block production.',
  'It does not apply to Arbitrum One, Robinhood Chain and Elysium (Nitro), Polygon (bor), BNB Smart Chain (geth-bsc for production; reth-bsc followers are covered by F-133), Avalanche (avalanchego) and Monad, none of which has the reth engine tree. HyperEVM blocks come from a closed node; its nanoreth replicas pin a reth cache that clears a destroyed account, as earlier cycles recorded. Tempo runs reth and was included in the live comparison above.',
  'state/cleared.json entries on non-reth networks and HyperEVM nanoreth; web3_clientVersion 2026-11-27')

leads = [
    {'chainIds': [10, 8453, 130, 57073, 1868], 'lens': 'L2',
     'question': 'Task 1 of L-1235 is still open: lift the revm 43.0.2 journal entry points (load account and slot with the hashbrown lookup, sstore with its journal entry, checkpoint, checkpoint_commit, checkpoint_revert and the transient map) from the op-reth v2.10.0-rc.4 and Base v1.5.6 x86-64 binaries in cycles/032/theme-opstack-reth-binary-lift.work/dl, and run journal_seq.py and the PoolManager shapes on real tables in model memory.',
     'why': 'This cycle did not start the lift. The journal is tested only live (15,000 nested-frame sequences in cycle 32), so a fault on inputs those sequences never produced would still be unseen.',
     'priority': 'medium'},
    {'chainIds': [480], 'lens': 'L2',
     'question': 'Task 4 binary part of L-1265: fetch ghcr.io/worldcoin/world-chain:v2.8.2, check its digest, and compare its instruction table, 25 arithmetic, comparison and shift handlers, jump analysis and storage handlers with the lifted op-reth code using cycles/033/.../cmp_reth.py.',
     'why': 'The lockfile shows the same revm-interpreter 43.0.2 and ruint 1.20.0 as op-reth v2.10.0-rc.4, but compiled code was not compared and the image was not fetched this cycle.',
     'priority': 'low'},
    {'chainIds': [10, 8453], 'lens': 'L2',
     'question': 'Task 5: plant the five journal faults (revert restoring zero, revert restoring the committed value, skipped entry, checkpoint index off by one, probe stopping one group early) in the lifted journal once Task 1 exists, and show the checks catch each.',
     'why': 'Without the planted faults the Task 1 runs would not show that the checks can see a fault.',
     'priority': 'low'},
    {'chainIds': [4326], 'lens': 'L2',
     'question': 'Which reth revision mega-reth v2.3.1 (the build mainnet.megaeth.com answers) pins for reth-engine-tree and reth-execution-cache.',
     'why': 'The cache rules for MegaETH were read at reth v2.3.0 on the assumption that mega-reth builds on it; mega-reth is not public.',
     'priority': 'low'},
]

lead_results = [
    {'leadId': 'L-1235', 'outcome': 'inconclusive',
     'answer': 'The binary lift of the journal was not done in this cycle. The live check was extended instead: 2,477 PoolManager slots on 13 reth-derived endpoints read the same through eth_getStorageAt and through extsload at the writing block and the next one, and 248 slot0 and liquidity words equal the values in the block\'s own Swap events.'},
    {'leadId': 'L-1260', 'outcome': 'cleared',
     'answer': 'At reth v2.11.0 and at the revisions behind op-reth v2.8.1 and v2.10.0-rc.4, Base v1.5.6, X Layer v0.0.7, Celo and reth v2.3.0, the execution cache keys every entry by the full code hash, address or (address, slot) pair, fills only with post-block values or parent-state reads, is saved only after all prewarm work ends, is dropped on an invalid block and cleared on a fork. Prewarm, txpool snapshots and block access list prefetch never insert a speculative write. No case gives a later block a word that differs from the state of an address with code, so no PoolManager read can be stale.'},
    {'leadId': 'L-1265', 'outcome': 'inconclusive',
     'answer': 'world-chain v2.8.2 runs revm 43.0.3, revm-interpreter 43.0.2 and ruint 1.20.0 like op-reth v2.10.0-rc.4; keccak-asm 0.1.8 assembles the same keccak source for default builds. The image was not fetched and the compiled handlers were not compared.'},
]

doc = {'unit': 'theme-reth-journal-and-execution-cache', 'profiles': [], 'findings': [], 'cleared': cleared,
       'leads': leads, 'leadResults': lead_results}
json.dump(doc, open(OUT, 'w'), indent=1)
print(OUT)
