#!/usr/bin/env python3
"""Writes theme-monad-exit-writer.research.json from the outputs in out/."""
import json, re, os, glob
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = 'research/network-risk/cycles/018/theme-monad-exit-writer.work'
E = 'research/network-risk/cycles/016/theme-monad-harness-exact.work/dl/monad-0.16.5/category/vm/compiler/ir/x86'
ALL = [json.loads(l) if False else None for l in []]

def kv(line):
    return dict(re.findall(r'(\S+?)=(\S+)', line))

perm = [kv(l) for l in open(f'{W}/out/perm-0-720.txt') if l.startswith('mode=')]
shuf = [kv(l) for l in open(f'{W}/out/shuffle-1-200.txt') if l.startswith('mode=')]
f1 = [kv(l) for l in open(f'{W}/out/fault1.txt') if l.startswith('mode=')]
f3 = [kv(l) for l in open(f'{W}/out/fault3.txt') if l.startswith('mode=')]
for s in perm + shuf:
    assert s['bad_final'] == '0' and s['digest'] == perm[0]['digest'] and s['nonzero_after_cycles'] == '0'
p0 = perm[0]
f3bad = sorted(int(x['bad_final']) for x in f3)
f1bad = sorted(int(x['bad_final']) for x in f1)

# mined replay
mined = {}
for f in sorted(glob.glob(f'{W}/out/mined2/*.out')):
    b = os.path.basename(f)[:-4]
    order = b.rsplit('-part', 1)[0]
    t = [l for l in open(f) if l.startswith('txs=')]
    d = kv(t[-1]) if t else {'txs': '0', 'mismatches': 'NA'}
    m = mined.setdefault(order, {'txs': 0, 'mismatches': 0, 'divergences': 0, 'frames': 0, 'frames_match': 0, 'parts': 0})
    m['parts'] += 1
    for k in ('txs', 'mismatches', 'divergences', 'frames', 'frames_match'):
        m[k] += int(d.get(k, 0)) if d.get(k, '0').isdigit() else 0
json.dump(mined, open(f'{W}/out/mined2/aggregate.json', 'w'), indent=1)
clean = {k: v for k, v in mined.items() if '-f0' in k}
faulted = {k: v for k, v in mined.items() if '-f3' in k}
for k, v in clean.items():
    assert v['parts'] == 4 and v['txs'] == 2007 and v['mismatches'] == 0 and v['divergences'] == 0, (k, v)
fv = list(faulted.values())[0]

cv = open(f'{W}/out/rpc/clientversion.txt').read()

src = lambda l, s: {"url": f"{E}/emitter.cpp:{l}", "supports": s}
vs = lambda l, s: {"url": f"{E}/virtual_stack.cpp:{l}", "supports": s}

cleared = [
 {"chainIds": [143], "lens": "L1",
  "check": "L-840 question 1. Does the spill step before the dependency loop of Emitter::write_to_final_stack_offsets in monad v0.16.5 remove every dependency cycle?",
  "result": ("No, and it does not need to. The spill step (emitter.cpp:1401-1418) only frees one AVX register as scratch (init_yx1): when no register is free it moves the value of the first unreserved AVX holder (virtual_stack.cpp:530-541) to memory, or drops the register when the element already has a stack offset, general register or literal (virtual_stack.cpp:553-565). It runs before the dependency count is built at 1433-1461, so a spilled element is counted as a memory element. Cycles are left for the second loop (1564-1621). The dependency relation is a function: an element has at most one stack offset, so it blocks at most one other element (the owner of that offset). Every element that is not on a cycle is reached from a leaf and is written in the first loop (1478-1542), so after it exactly the cycle members have a count, and that count is 1. The second loop rotates each cycle through two AVX registers. yx1 is init_yx1 and yx2 is a free register or, when none is free, the register of the last AVX element written in the first loop (1550-1561). When no register is free, 15 of the 16 registers belong to elements other than init1; at most one of them (the popped jump target) is off the stack, so at least 14 AVX stack elements are written in the first loop and yx1 != yx2 holds in every order. Each cycle member's slot is read before it is overwritten, because the slots of a cycle are final indices of its own members only and stack indices of distinct elements are disjoint. The iteration order of the map decides which cycle is rotated first and which register serves as yx2; neither changes a stored word."),
  "source": f"{E}/emitter.cpp:1401-1418 ; {E}/emitter.cpp:1433-1461 ; {E}/emitter.cpp:1550-1621 ; {E}/virtual_stack.cpp:530-565 ; https://cdn.jsdelivr.net/gh/category-labs/monad@v0.16.5/category/vm/compiler/ir/x86/emitter.cpp"},
 {"chainIds": [143], "lens": "L1",
  "check": "L-840 question 2. Is a dependency skipped at the AVX register check (emitter.cpp:1457-1459) ever read later from a register that an earlier write in the loop reassigned?",
  "result": ("No. Every register write the writer emits goes to yx1 or yx2: the loads at 1496, 1499 and 1511 in the first loop and 1588-1598 in the cycle loop. In the first loop yx1 is init_yx1 until the first AVX element is popped, and from then on it is the register of the AVX element popped most recently (1484-1487). An AVX element x whose memory slot is a final index of another element e is not counted as a blocker of e, so e may be written over x's slot first. x is then read from its own register when it is popped. That register can be overwritten only after it became yx1, which happens when x itself is popped, and x is fully written by then. init_yx1 is a register no stack element holds. AVX elements are never on a cycle, because they have no outgoing edge, so all of them are written in the first loop, before any cycle-loop write to yx1 or yx2. The writer writes no general register: mov_general_reg_to_mem (1833-1840) only reads them, and mov_literal_to_ymm (1961-1988) writes only the target ymm and does not change flags. The pc of a popped jump target is taken into its operand before the writer runs (3544-3576)."),
  "source": f"{E}/emitter.cpp:1457-1459 ; {E}/emitter.cpp:1478-1542 ; {E}/emitter.cpp:1833-1840 ; {E}/emitter.cpp:1961-1988 ; {E}/emitter.cpp:3544-3576"},
 {"chainIds": [143], "lens": "L1",
  "check": "L-840 question 3. Can an element whose stack offset lies below min_delta be left with a nonzero dependency count?",
  "result": ("No element has such an offset. Stack offsets come from three places only: the entry elements of each index from -1 down to the new min_delta (virtual_stack.cpp:298-302 and 326-330), the positive offsets 0..max_delta-1 (305-308, 334-337) and offsets that a destroyed or moved element returned (free_stack_offset, 202-208), all of which were handed out from the first two. min_delta never rises inside a block (continue_block takes the minimum, 321). Stack::get also asserts its index is at most top_index and at() asserts it is inside negative_elems_ (365-383). An offset above top_index is skipped at 1450 and creates no count. Any element with a count after the first loop is on a cycle and has its count set to zero at 1577-1579. The instrumented build counted offset_below_min=0 and nonzero_after_cycles=0 in every compile."),
  "source": f"{E}/virtual_stack.cpp:281-344 ; {E}/virtual_stack.cpp:365-383 ; {E}/emitter.cpp:1446-1452 ; {E}/emitter.cpp:1564-1580"},
 {"chainIds": [143], "lens": "L1",
  "check": "L-840 task 2. The block-exit writer of v0.16.5 run in every forced order on the deployed Monad PoolManager runtime (24,009 bytes, the cycle 16 copy monad-pm-runtime.hex, sha256 9f68b8fc of the hex file), with a symbolic check of every block exit and a runtime replay of mined transactions.",
  "result": (f"The writer was rebuilt from the v0.16.5 file (sha256 1294ce58, equal to the jsDelivr copy fetched here) with both loops over dep_counts taken from a vector holding the same keys (src/patch_writer.py). The emitted instructions are the original ones in the forced order. Each emitted load and store also drives a symbolic machine, and at every block exit each final index must hold the element that owns it. One compile of the PoolManager has {p0['calls']} block exits with something on the stack, {p0['elems_total']} stack elements in all, at most {p0['max_elems']} elements and {p0['max_deps']} blocked elements in one exit, {p0['avx_skipped']} dependencies skipped at the AVX check, {p0['cycles']} cycles (longest {p0['max_cycle_len']}) and no exit that has to spill an AVX register. Exits by element count: 1 to 6 elements {sum(int(x) for x in p0['hist1-6'].split(','))}, 7 to 15 {p0['h7-15']}, 16 or more {p0['h16+']}. Permutation indices 0 to 719 gave every block with up to 6 elements all its orders, with a seeded shuffle for larger ones (seed = index), and shuffle seeds 1 to 200 reordered every block: 920 compiles, 0 wrong final words, 0 AVX elements read after their register was overwritten, and the same final-state digest {p0['digest']} as the map's own order. The orders do change the machine code: two forced orders differ by 2,312 to 3,306 lines of the 48,757-line asm log. Two planted faults show the check can fail: one temporary register for cycles gave {f1bad[0]} to {f1bad[-1]} wrong words per compile, and rereading AVX elements from memory gave {f3bad[0]} to {f3bad[-1]} wrong words depending on the order (200 seeds). At run time the instrumented build replayed the 2,007 mined Monad PoolManager transactions of cycle 16 from their pre-state under {len(clean)} orders (map order, permutation indices 1 to 5, shuffle seeds 101 to 106): {sum(v['txs'] for v in clean.values())} transaction runs, 0 mismatches between interpreter and native code, 0 divergences from the block. With the planted reread fault {fv['mismatches']} of 2,007 transactions mismatched. The runtime comparison is per transaction frame, not per block exit; the per-exit comparison is the symbolic one."),
  "source": f"{R}/src/patch_writer.py ; {R}/out/perm-0-720.txt ; {R}/out/shuffle-1-200.txt ; {R}/out/fault1.txt ; {R}/out/fault3.txt ; {R}/out/mined2/aggregate.json"},
 {"chainIds": [143], "lens": "L1",
  "check": "Whether the read-only data that the writer's literal loads use depends on the order.",
  "result": "The order changes where a literal lands in the read-only table, not its value. RoData keys each entry by its bytes and returns the offset of the existing entry on a repeat (emitter.cpp:339-436). Full-width literals are 32-byte entries at 32-byte offsets, which vmovaps needs; 16, 8 and 4 byte entries are read with vmovups, vmovq and vmovd, which need no alignment.",
  "source": f"{E}/emitter.cpp:339-436 ; {E}/emitter.cpp:1961-1988"},
]

cleared.append(
 {"chainIds": [143], "lens": "L1",
  "check": "L-812 and L-849. Which Monad release mainnet validators run, from headers, RPC client strings and release records.",
  "result": "The release page lists v0.16.5 as released to mainnet on 2026-10-22 and v0.16.7 as released to testnet on 2026-11-19 with mainnet N/A; the monad-bft v0.16.7 release tells operators not to upgrade without an announcement, and the v0.16.7 upgrade page says it applies to testnet only. The latest mainnet header has extraData of 32 zero bytes and no version field, and admin_nodeInfo is disabled on rpc3.monad.xyz. web3_clientVersion on 2026-11-25 (out/rpc/clientversion.txt): Monad/0.16.7 on rpc.monad.xyz, rpc1.monad.xyz, rpc-mainnet.monadinfra.com and the Tatum gateway; Monad/unknown on rpc3.monad.xyz, rpc4.monad.xyz and Ankr; proxy strings on rpc2.monad.xyz (eRPC), Originstake (eRPC), dRPC and thirdweb. So validators are on v0.16.5 by the published schedule while some mainnet full nodes run v0.16.7. No vote, proposal or validator-set field naming a version was found. This unit shows that the two releases store the same words at every block exit, so the mix gives no split.",
  "source": "https://docs.monad.xyz/developer-essentials/changelog/releases ; https://github.com/category-labs/monad-bft/releases/tag/v0.16.7 ; https://docs.monad.xyz/node-ops/upgrade-instructions/v0.16.7 ; eth_getBlockByNumber latest and web3_clientVersion on the endpoints named, 2026-11-25"})

leads = [
 {"chainIds": [143], "lens": "L1",
  "question": "When mainnet validators move from v0.16.5 to a later release, rerun the cycle 17 site tests and this unit's order sweep (src/build.sh, build/orders-165w) on that release's emitter.",
  "why": "The proof covers v0.16.5's writer and v0.16.7's vector-ordered copy of the same algorithm; a release that changes the writer itself needs the symbolic check again.",
  "priority": "low"},
]

leadResults = [
 {"leadId": "L-840", "outcome": "cleared",
  "answer": "Every iteration order of dep_counts in the v0.16.5 block-exit writer stores the same words at the same stack slots. The argument from emitter.cpp and virtual_stack.cpp is in cleared items 1 to 3. 920 compiles of the deployed PoolManager under forced orders (all orders of each block with up to 6 elements, 200 seeded shuffles of larger blocks) passed a symbolic check of all 659 block exits each, and 12 orders replayed the 2,007 mined transactions without a mismatch. Planted faults were caught by both tests."},
 {"leadId": "L-849", "outcome": "inconclusive",
  "answer": "Block headers carry no version: extraData of the latest block is 32 zero bytes, and admin_nodeInfo is disabled. The Monad release page lists v0.16.5 for mainnet (2026-10-22) and v0.16.7 for testnet only (2026-11-19, mainnet N/A), and announcement #15 is a testnet release. RPC nodes on mainnet answer Monad/0.16.7 (rpc.monad.xyz, rpc1.monad.xyz, rpc-mainnet.monadinfra.com, Tatum), Monad/unknown (rpc3, rpc4, Ankr), or a proxy string (eRPC, dRPC, thirdweb). Mainnet validators are therefore on v0.16.5 by the official schedule, with 0.16.7 full nodes beside them; no signed vote or proposal field was found that names the version. Both releases give the same results by this unit's proof, so the answer no longer changes a PoolManager result."},
 {"leadId": "L-812", "outcome": "cleared",
  "answer": "Settled as far as public data allows (see L-849): v0.16.5 is the mainnet release and some mainnet RPC nodes run v0.16.7. Both are covered by the cycle 16 and 17 harnesses, and the block-exit order dependence of v0.16.5 changes no stored word."},
]

out = {"unit": "theme-monad-exit-writer", "profiles": [], "findings": [], "cleared": cleared,
       "leads": leads, "leadResults": leadResults}
p = os.path.join(W, '..', 'theme-monad-exit-writer.research.json')
json.dump(out, open(p, 'w'), indent=1)
print('wrote', os.path.abspath(p))
print(json.dumps({k: v for k, v in mined.items()}, indent=0)[:2000])
