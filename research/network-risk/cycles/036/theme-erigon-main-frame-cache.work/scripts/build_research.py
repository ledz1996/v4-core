import json, os
W = 'research/network-risk/cycles/036/theme-erigon-main-frame-cache.work'
C = '0ae25bfbdaee8653f1a97c8a4ad844fba24106d3'
RM = 'https://raw.githubusercontent.com/erigontech/erigon/main/'
R382 = 'https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/'
ALL = [x['chainId'] for x in json.load(open('research/network-risk/state/networks.json'))['networks']]
NON = [c for c in ALL if c != 1]

seq = json.load(open(W + '/out/seqs.json'))
pmn = json.load(open(W + '/out/pmshapes-none.json'))['totals']
pmf = {f: json.load(open(W + f'/out/pmshapes-{f}.json'))['totals'] for f in ['nested', 'revert', 'revshort', 'revshort-epoch', 'noaddr', 'reuse']}
nested_mm = json.load(open(W + '/out/pmshapes-nested.json'))['mismatches']
ret_diff = sum(1 for m in nested_mm if not m['same']['ret'])
rn = seq['random']

def caught(f): return sorted(k for k, v in seq['sequences'][f].items() if v['stale'])

findings = [{
    "ref": "F-165",
    "title": "Erigon's per-frame SLOAD cache already ships in releases v3.8.0 to v3.8.2, and it keys correctly on the journal length and epoch",
    "chainIds": [1],
    "lens": "L1",
    "assumptions": ["A10", "A1"],
    "effect": "degrade",
    "actor": "operator",
    "severity": "info",
    "difference": "Erigon keeps the last two SLOAD results of each call frame and serves a repeat read from them while IntraBlockState.ReadStamp() is unchanged. F-165 said only main has this cache. That is wrong: the same frameSlots code is in the tags v3.8.0, v3.8.1 and v3.8.2 and in release/3.8. It is not in v3.7.0 or v3.7.1. Geth, reth and Nethermind have no such cache.",
    "mechanism": "ReadStamp is {len(journal.entries), journal.epoch} (main read_paths.go:1573-1587, v3.8.2 read_paths.go:1804-1818). Every write pushes a journal entry: SetState unless the value is unchanged, transient storage, balance, access-list warming, self-destruct and create. revert truncates the journal to the snapshot and bumps the epoch, and Reset bumps the epoch too (journal.go:116-157). So a write by any frame, at any address or depth and through any call type, moves the stamp, and so does any revert. The PoolManager's reentry shape works like this. swap reads slot0 at src/PoolManager.sol:196 through Pool.checkPoolInitialized (src/libraries/Pool.sol:585-586), then calls beforeSwap at :202, where the hook may reenter and write the pool, and then reads the pool again in _swap at :206 and Pool.swap at src/libraries/Pool.sol:283. modifyLiquidity does the same at src/PoolManager.sol:154-156 and Pool.sol:207. When the nested frame writes, the outer frame's entries no longer match the stamp, so the outer frame reads the slot afresh. In a model of the cache copied line by line from the erigon source, the unchanged code gave no stale word. A planted fault that skips the stamp bump on reentrant writes made the outer frame read stale TickBitmap words (src/libraries/TickBitmap.sol:73) and return different swap and liquidity amounts. That shows the shape is the right test.",
    "impact": "None for funds. The cache returned no stale word in any sequence or PoolManager reentry run. Even a fault here would only change what an erigon node computes. On a validator that means a state root the other clients reject. On an RPC node it means wrong eth_call quotes. An ordinary account cannot move pool funds through it.",
    "preconditions": "This is a consensus fault, not an exploit. It would need a future erigon change that writes storage without a journal entry, or edits a journal entry in place, while the cache stays on.",
    "mitigations": "Rerun scripts/seqs.py and scripts/pmshapes.py on each erigon release that touches execution/state or execution/vm. Keep a mix of clients among validators.",
    "coreRefs": ["src/PoolManager.sol:154-156", "src/PoolManager.sol:196-206", "src/libraries/Pool.sol:283", "src/libraries/Pool.sol:585-586", "src/libraries/TickBitmap.sol:73"],
    "sources": [
        {"url": RM + "execution/state/read_paths.go", "supports": "lines 1573-1587: ReadStamp = {len(journal.entries), journal.epoch}; off only under TraceTransactionIO (main, commit " + C + ")"},
        {"url": RM + "execution/state/journal.go", "supports": "lines 99-157: epoch bumped on Reset and revert; push only appends; revert truncates to the snapshot"},
        {"url": RM + "execution/vm/interpreter.go", "supports": "lines 124-171 frameSlots, lookupSlot, put; 243-272 putCallContext clears ok[]; 577-578 on set from ReadStamp"},
        {"url": RM + "execution/vm/instructions.go", "supports": "lines 859-880 opSload served from the cache"},
        {"url": R382 + "execution/vm/interpreter.go", "supports": "the same frameSlots cache in released v3.8.2 (also v3.8.0, v3.8.1, release/3.8; absent in v3.7.0, v3.7.1)"},
        {"url": R382 + "execution/state/read_paths.go", "supports": "lines 1804-1818: the same ReadStamp in v3.8.2"},
        {"url": "local run: " + W + "/out/pmshapes-none.json", "supports": f"{pmn['scenarios']} reentry scenarios, {pmn['sloads']} SLOADs, {pmn['hits']} cache hits, 0 stale, 0 mismatches"},
    ],
    "evidence": "primary",
}]

cleared = [
    {"chainIds": [1], "lens": "L1",
     "check": f"Task 1: where the stamp is defined and every place that changes it, at erigon main ({C}, version 3.9.0-dev in db/version/app.go:33-36) and at v3.8.2.",
     "result": "ReadStamp is in execution/state/read_paths.go (main :1573-1587, v3.8.2 :1804-1818). Cycle 35 could not find it because it guessed the wrong file names; sourcegraph's index of the repository found it. "
               "These change the stamp. SetState pushes storageChange unless prev == value (intra_block_state.go:1537-1561; in v3.8.2, stateObject.SetState state_object.go:238-279 and setStateVersioned :1856-1880). A same-value write needs no bump. "
               "Transient storage pushes transientStorageChange when the value changes (transient_storage.go:52-64). Self-destruct pushes selfdestructChange (:1623-1671). Account creation pushes createObjectChange or resetObjectChange. "
               "Access-list warming is journalled (:2385-2398), and SLOAD's gas phase warms before the read whose stamp it stores. revert truncates and bumps the epoch, and Reset or EndTransaction bumps the epoch (journal.go:116-157, intra_block_state.go:2306-2314). In v3.8.2, updateAccount also bumps the epoch at finalization (:2599). "
               "The journal is one per IntraBlockState, so a write by another frame at the same address, by a DELEGATECALL frame running other code on the same storage, or at any other address moves the stamp the same way. "
               "There is no in-place edit of a journal entry and no coalescing of writes (journal.go push and every constructor append). "
               "These paths write without a journal entry. SetStorage (:1566-1593) is used only for debugging and state overrides before execution, and in v3.8.2 it goes through journalled fakeStorage. SetIncarnation (:1597-1607) has callers only in genesis writing, t8n, test utilities and the state layer, none of them the vm (sourcegraph search). "
               "In the parallel executor the stamp ignores versionMap. A repeat read returns the first read's value, which is the value the read set records, and Block-STM validation covers it. Funds are not affected.",
     "source": RM + "execution/state/read_paths.go ; " + RM + "execution/state/journal.go ; " + RM + "execution/state/intra_block_state.go ; " + RM + "execution/state/transient_storage.go ; " + R382 + "execution/state/state_object.go"},
    {"chainIds": [1], "lens": "L1",
     "check": f"Task 2 (L-1298): the cache, transcribed line by line into Python (scripts/cachemodel.py), on sequences (a) to (h) plus c2, c3 and a transient-storage case, and on {seq['trees']} random frame trees (seed {seq['seed']}), each compared with the state the reads should see.",
     "result": f"There was no stale word in any sequence. In the random trees there were {rn['none']['reads']} reads, {rn['none']['hits']} cache hits and 0 stale reads. "
               "The sequences were: (a) a nested write by the same contract; (b) the nested frame reverting; (c) a deeper frame reverting only itself; (d) a write through DELEGATECALL; (e) two entries in use, then a third slot evicting one; (f) a slot written back to its original value; (g) reads in a STATICCALL frame; (h) sibling frames reusing the parked context. "
               "Why the epoch is not needed inside a transaction: a frame stores its entries at journal length L. A revert can only truncate to a snapshot that some live frame took at or after L, so if the length returns to L, entries 0 to L-1 are unchanged and the state is the same. The epoch matters at Reset.",
     "source": W + "/out/seqs.json ; " + W + "/scripts/seqs.py"},
    {"chainIds": [1], "lens": "L1",
     "check": f"Task 2, PoolManager runtime of research/network-risk/build/PoolManager.json run in tools/opdiff/pyevm.py with and without the cache model: {pmn['scenarios']} scenarios (seed 3620261128). In each, a hook on its own pool reenters the PoolManager from beforeSwap, beforeAddLiquidity, beforeRemoveLiquidity or beforeDonate. The nested work is a swap, swaps both ways, a donate, an add and remove of the same position (storage written back), a nested list that reverts, or unlock-free calls (initialize of another pool, approve, setOperator, transfer, extsload).",
     "result": f"Every SLOAD value, every SSTORE, the returned record of every call (deltas, and extsload reads of slot0, liquidity and fee growth after each step) and the final storage were equal in all {pmn['scenarios']} scenarios. There were {pmn['sloads']} SLOADs, {pmn['hits']} cache hits, {pmn['sstores']} SSTOREs and {pmn['reentrantPmWrites']} storage writes by PoolManager frames nested under a hook, with 0 stale reads. "
               "The model leaves out erigon's access-list, refund, nonce and touch entries, so it hits the cache at least as often as erigon would.",
     "source": W + "/out/pmshapes-none.json ; " + W + "/scripts/pmshapes.py"},
    {"chainIds": [1], "lens": "L1",
     "check": "Task 5: faults planted in the cache model.",
     "result": f"nested (a reentrant write does not bump the stamp): caught by sequences {caught('nested')}, {rn['nested']['trees_with_stale']} random trees, and {pmf['nested']['mismatch']} of {pmf['nested']['scenarios']} PoolManager scenarios ({pmf['nested']['stale']} stale reads, all TickBitmap words -1 and 0, with the returned amounts changed in {ret_diff}). "
               f"revshort (revert truncates one entry short and does not bump the epoch): caught by {caught('revshort')} and {rn['revshort']['trees_with_stale']} trees. With the epoch bumped (revshort-epoch) it is not caught, which shows the epoch's role. "
               f"noaddr (one cache keyed by slot only): caught by {caught('noaddr')} and {rn['noaddr']['trees_with_stale']} trees. reuse (ok[] kept across frame reuse): caught by {caught('reuse')} and {rn['reuse']['trees_with_stale']} trees. "
               "The PoolManager runs do not catch noaddr or reuse, because in them only the PoolManager uses SLOAD (the hook and token doubles use transient storage). "
               "revert (truncation right, no epoch bump) is not caught anywhere, and it cannot be observed inside a transaction, as argued above.",
     "source": W + "/out/seqs.json ; " + W + "/out/pmshapes-nested.json ; " + W + "/out/pmshapes-revshort.json ; " + W + "/out/pmshapes-noaddr.json ; " + W + "/out/pmshapes-reuse.json"},
    {"chainIds": [1], "lens": "L1",
     "check": "Task 3: the first 20 reentry scenarios sent by eth_call with state overrides to public endpoints, bracketed with web3_clientVersion.",
     "result": "ethereum-mainnet.gateway.tatum.io reports erigon/3.8.2-8a3f3b2c, which carries the cache, but refused eth_call ('available for paid plans only'). This was recorded and not worked around. No other public endpoint reporting erigon 3.8.x or a main build was found. eth.blocktailor.com (erigon/3.7.1, no cache) and ethereum-rpc.publicnode.com (reth/v2.11.0) returned the reference interpreter's bytes in 20 of 20 scenarios.",
     "source": W + "/out/rpcshapes.json ; " + W + "/out/clientversions.txt"},
    {"chainIds": [1], "lens": "L1",
     "check": "Task 4 (L-1285): whether a 3.9.0 tag or release branch exists, and the integer library pins.",
     "result": "On 2026-11-27, raw.githubusercontent.com answers 404 for go.mod at v3.9.0, v3.9.0-rc1, v3.9.0-beta, release/3.9 and release/v3.9. main is 3.9.0-dev, needs go 1.26.8 and pins uint256 808a9d02b85f. v3.8.2 and release/3.8 pin 087f4b32f234. There is nothing to rerun yet. On the day 3.9.0 is tagged, fetch its interpreter.go, instructions.go, read_paths.go and journal.go, diff them against dl/main, and run scripts/seqs.py and scripts/pmshapes.py, along with cycle 35's erigon_fastpaths.py against the pinned uint256.",
     "source": "https://raw.githubusercontent.com/erigontech/erigon/main/go.mod ; https://raw.githubusercontent.com/erigontech/erigon/v3.8.2/go.mod ; https://raw.githubusercontent.com/erigontech/erigon/main/db/version/app.go"},
    {"chainIds": NON, "lens": "L1",
     "check": "Whether any of the other 20 networks runs erigon-derived node software that would inherit the cache.",
     "result": "No. Polygon: Erigon dropped official Polygon support after v3.1.0, and Polygon's fork (0xPolygon/erigon, release/3.2-develop) has no frameSlots and was sunset on 1 August 2026. The Polygon endpoints report bor. BNB Chain: bsc-erigon (node-real, main) has no frameSlots and reached end of life at the end of 2025. BNB endpoints report Geth/v1.8.2 or reth-bsc. X Layer reports reth/xlayer. The other networks report op-reth, reth, nitro, avalanchego, Monad, mega-reth, tempo, arc or hyperliquid. This theme does not apply to them.",
     "source": "https://erigon.tech/blog/an-update-on-our-support-for-polygon/ ; https://forum.polygon.technology/t/sunsetting-erigon-support/21872 ; https://raw.githubusercontent.com/0xPolygon/erigon/release/3.2-develop/core/vm/interpreter.go ; https://www.bnbchain.org/en/blog/important-update-bnb-chain-client-support-and-erigon-sunset ; https://raw.githubusercontent.com/node-real/bsc-erigon/main/core/vm/interpreter.go ; " + W + "/out/clientversions.txt"},
]

leads = [{"chainIds": [1], "lens": "L1",
          "question": "Find a public erigon 3.8.x endpoint that answers eth_call (or a released erigon 3.9.0) and send scripts/rpcshapes.py's 20 reentry scenarios to it. Do they return the reference interpreter's bytes?",
          "why": "The cache was tested here only in a transcription. The one erigon 3.8.2 endpoint found refuses eth_call on its free plan.",
          "priority": "low"}]

leadResults = [
    {"leadId": "L-1298", "outcome": "cleared", "answer": f"ReadStamp is defined in execution/state/read_paths.go as {{len(journal.entries), journal.epoch}}. Every storage write, including writes by nested frames of the same contract and by DELEGATECALL frames, pushes an entry, and every revert truncates and bumps the epoch. In the outer-read, nested-write, outer-read shape the outer read misses and returns the new word. Model: 0 stale reads in sequences (a)-(h) and {seq['trees']} random trees. PoolManager reentry under pyevm: 0 mismatches in {pmn['scenarios']} scenarios. The cache also ships in v3.8.0-v3.8.2."},
    {"leadId": "L-1285", "outcome": "inconclusive", "answer": "There is no v3.9.0 tag and no release/3.9 branch as of 2026-11-27. main pins uint256 808a9d02b85f and release/3.8 pins 087f4b32f234. The rerun steps are recorded for the day 3.9.0 is tagged."},
]

out = {"unit": "theme-erigon-main-frame-cache", "profiles": [], "findings": findings, "cleared": cleared, "leads": leads, "leadResults": leadResults}
json.dump(out, open('research/network-risk/cycles/036/theme-erigon-main-frame-cache.research.json', 'w'), indent=1)
