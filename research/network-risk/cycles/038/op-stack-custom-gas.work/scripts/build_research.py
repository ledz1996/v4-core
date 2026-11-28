"""Cycle 38 op-stack-custom-gas: assemble the research file from the work directory outputs."""
import json, glob, os
NR = '/home/user/v4-core/research/network-risk'
WD = 'cycles/038/op-stack-custom-gas.work/'
W = NR + '/' + WD
FORNO = 'https://forno.celo.org'; XL = 'https://rpc.xlayer.tech'
fmt = lambda n: f'{n:,}'

def load(p):
    return json.load(open(W + p))

# replay of the rest of the cycle 36 window (L-1306)
win = load('replay/lwindow-rest.json')
rows = []
for f in sorted(glob.glob(W + 'replay/lazy_*.jsonl')):
    for line in open(f):
        try: rows.append(json.loads(line))
        except Exception: pass
# reruns with a higher lazy-load round limit replace the first record of the same transaction
if os.path.exists(W + 'replay/rerun_nc.jsonl'):
    rr = {}
    for line in open(W + 'replay/rerun_nc.jsonl'):
        try: d = json.loads(line); rr[d['tx']] = d
        except Exception: pass
    rows = [rr.get(r['tx'], r) for r in rows]
oc = {'match': 0, 'prefix': 0, 'otherlogs': 0, 'infra': 0, 'notConverged': 0, 'differ': 0}
slots = pmlogs = celo = 0; blocks = []; differ = []
for r in rows:
    blocks.append(r.get('block'))
    celo += r.get('celoTransfers') or 0
    if r.get('match'):
        oc['match'] += 1; pmlogs += r.get('pmLogs') or 0; slots += r.get('pmSlotsCompared') or 0; continue
    p = r.get('prefix')
    if isinstance(p, dict) and p.get('match'):
        oc['prefix'] += 1; pmlogs += p.get('pmLogs') or 0; slots += p.get('pmSlotsCompared') or 0; continue
    if r.get('statusChain') is None:
        oc['infra'] += 1; continue
    pm_ok = r.get('statusChain') == r.get('statusRef') and r.get('pmLogsEqual') and not r.get('pmSlotMismatch') and r.get('pmNativeEqual') is not False
    if pm_ok: oc['otherlogs'] += 1; continue
    if not r.get('converged') and not (isinstance(p, dict) and p.get('converged')):
        oc['notConverged'] += 1; differ.append(r['tx']); continue
    oc['differ'] += 1; differ.append(r['tx'])
n = len(rows); remaining = len(win['txs']) - n
blocks = [b for b in blocks if b]
summary = dict(oc, n=n, windowRest=len(win['txs']), notRun=remaining, pmSlots=slots, pmLogs=pmlogs, celoTransfers=celo,
               blockMin=min(blocks) if blocks else None, blockMax=max(blocks) if blocks else None, differ=differ)
json.dump(summary, open(W + 'replay/summary.json', 'w'), indent=1)

sw = {r['chainId']: r for r in load('out/swaps.json')['results']}
forno_cv = open(W + 'out/forno-clientver.txt').read().split('\n')
geth_n = sum(int(l.split()[0]) for l in forno_cv if 'Geth' in l)
reth_n = sum(int(l.split()[0]) for l in forno_cv if 'reth' in l)

def lg(name):
    return open(W + 'out/' + name).read()
for name, want in (('battery.log', 'mismatches 0 errors 0'), ('pmdiff.log', 'different 0 errors 0'), ('pmdiff2.log', 'identical 300/300 different 0'), ('targeted.log', 'mismatches 0 errors 0')):
    t = lg(name); assert t.count(want) == 2, (name, t[-500:])

rep_text = ("Of the %d window transactions that cycle 36 did not reach (blocks %s to %s of the cycle 24 window), %d ran in this cycle before the 50 minute shard limit: %d match outright, %d match after their block prefix, %d differ only in logs of other contracts with PoolManager status, logs, words and native balance equal, %d could not run because no endpoint served a receipt, %d stopped at the lazy-load round limit before all of their state was fetched (the reference then reverts with no logs, a limit of the replay and no chain result), and %d differ in a PoolManager item after a converged run. %s PoolManager storage words and %d CELO transfer precompile calls were compared or modelled. %d transactions of the window are still not run."
            % (len(win['txs']), fmt(min(t[1] for t in win['txs'])), fmt(max(t[1] for t in win['txs'])), n, oc['match'], oc['prefix'], oc['otherlogs'], oc['infra'], oc['notConverged'], oc['differ'], fmt(slots), celo, remaining))

C = sw[42220]; X = sw[196]
rerun_text = ("battery.py 99,985 vectors and targeted.py 85,544 vectors gave 0 mismatches and 0 errors on both endpoints; pmdiff.py 250 of 250 and pmdiff2.py 300 of 300 scripts identical to the Ethereum reference; swaps.py found Celo %d mined swaps in blocks %s to %s and X Layer %d in blocks %s to %s, all with the exact tick relation; Celo %d and X Layer %d pairs, with the %d Celo multi-step swaps replayed by replay.py with 0 failures."
              % (C['swaps'], fmt(C['blocks'][0]), fmt(C['blocks'][1]), X['swaps'], fmt(X['blocks'][0]), fmt(X['blocks'][1]), C['pairs'], X['pairs'], C['amount']['multi']))

src_pool = 'src/libraries/Pool.sol'
research = {
 "unit": "op-stack-custom-gas",
 "_lenses": ["L1", "L2", "L4", "L5"],
 "profiles": [
  {"chainId": 42220, "lens": "L1",
   "summary": "No release since cycle 36: the celo-reth build behind forno is still reth 74cc8bb (celo/reth-v1.0.10), and forno still sends a minority of requests to the op-geth c7ed55b8 build of F-116 (%d of %d calls this cycle). The reruns match and the deployed runtime has no byte outside push data that a new opcode such as CLZ could reinterpret." % (geth_n, geth_n + reth_n),
   "deltas": [
    {"delta": "web3_clientVersion on forno.celo.org, 30 calls on 2026-11-27: %d answered reth/v2.2.0-74cc8bb, %d answered Geth/v0.1.0-untagged-c7ed55b8-20260817 go1.24.13. Cycle 36 saw 1 op-geth answer in 6. Both builds answered the arithmetic subsets and all scripts in cycle 37, so the share changes nothing about results." % (reth_n, geth_n),
     "source": FORNO + " (web3_clientVersion); " + WD + "out/forno-clientver.txt", "relevance": "low"},
    {"delta": "The celo-kona tags page lists no tag after the celo/reth-v1.0 dependency backport (v1.0.10, cycle 36); main's registry configs.json is byte-identical to the copy cycle 36 saved, ending at jovian_time 1774958788 for chain 42220 with no karst_time.",
     "source": "https://github.com/celo-org/celo-kona/tags; https://raw.githubusercontent.com/celo-org/celo-kona/main/crates/kona/registry/etc/configs.json (" + WD + "raw/celo-configs.json)", "relevance": "none"}]},
  {"chainId": 42220, "lens": "L2", "summary": "The parent-storage replay of the Celo window moved %d transactions further; %d differ from the chain in a PoolManager item after a converged run, and %d did not converge." % (n, oc['differ'], oc['notConverged']),
   "deltas": [{"delta": rep_text, "source": FORNO + " and https://rpc.ankr.com/celo (eth_getStorageAt, eth_getCode, eth_getBalance, receipts); " + WD + "replay/summary.json, lazy_*.jsonl", "relevance": "none"}]},
  {"chainId": 42220, "lens": "L4", "summary": "Nothing new among the special addresses the PoolManager can reach; no Celo release or fork since cycle 36 adds or changes a predeploy.", "deltas": []},
  {"chainId": 42220, "lens": "L5",
   "summary": "Owner, protocol fee controller and deployed bytecode are unchanged since cycle 34.",
   "deltas": [{"delta": "At block 83,923,007 owner() returns 0x044aaf330d7fd6ae683eec5c1c1d1fff5196b6b7 (1,488 bytes of code, sha256 prefix afd409fdbeff0c42), protocolFeeController() returns zero, and the runtime is 24,009 bytes with sha256 prefix 86106cb2c6688f82, the value state/networks.json records.",
     "source": FORNO + " (eth_call 0x8da5cb5b and 0xf02de3b2, eth_getCode); " + WD + "out/l5.txt, out/code-42220.json", "relevance": "none"}]},
  {"chainId": 196, "lens": "L1",
   "summary": "No release since cycle 36: rpc.xlayer.tech answered reth/v2.3.0-f60420a xlayer/v0.0.7 to 10 of 10 calls. The reruns match, and the %d swaps the sequencer mined in blocks %s to %s satisfy the source math, which answers at the result level which instruction table block building uses." % (X['swaps'], fmt(X['blocks'][0]), fmt(X['blocks'][1])),
   "deltas": [
    {"delta": "The xlayer-reth tags page as served lists v0.0.7.3 (d32b20b, 20 October 2026) as its newest tag and does not show the v0.0.7.3-rc.1 tag of 5 November that cycle 36 read, so the page copy may be stale; no newer tag is visible. crates/chainspec/src/lib.rs on main is byte-identical to the cycle 36 copy and ends at XLAYER_MAINNET_JOVIAN_TIMESTAMP 1764691201.",
     "source": "https://github.com/okx/xlayer-reth/tags; https://raw.githubusercontent.com/okx/xlayer-reth/main/crates/chainspec/src/lib.rs (" + WD + "raw/xl-chainspec-lib.rs); " + WD + "out/xl-clientver.txt", "relevance": "none"}]},
  {"chainId": 196, "lens": "L2", "summary": "Nothing new on transaction boundaries or state changes outside the EVM this cycle.", "deltas": []},
  {"chainId": 196, "lens": "L4", "summary": "Nothing new among the special addresses the PoolManager can reach; the chainspec and releases are unchanged since cycle 36.", "deltas": []},
  {"chainId": 196, "lens": "L5",
   "summary": "Owner, protocol fee controller and deployed bytecode are unchanged since cycle 34.",
   "deltas": [{"delta": "At block 77,054,732 owner() returns 0x044aaf330d7fd6ae683eec5c1c1d1fff5196b6b7 (1,488 bytes, sha256 prefix afd409fdbeff0c42, the same code as on Celo), protocolFeeController() returns zero, and the runtime is 24,009 bytes with sha256 prefix 395c56a54ab2e08c as state/networks.json records.",
     "source": XL + " (eth_call 0x8da5cb5b and 0xf02de3b2, eth_getCode); " + WD + "out/l5.txt, out/code-196.json", "relevance": "none"}]},
 ],
 "findings": [],
 "cleared": [
  {"chainIds": [42220, 196], "lens": "L1",
   "check": "Reruns of battery.py, targeted.py, pmdiff.py, pmdiff2.py, swaps.py and replay.py for 42220 and 196 on forno.celo.org and rpc.xlayer.tech on 2026-11-27.",
   "result": rerun_text + " On forno the batches are samples over the reth and op-geth builds; cycle 37 showed each build keeps a batch on one build.",
   "source": WD + "out/battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.log, replay.log"},
  {"chainIds": [42220, 196], "lens": "L1",
   "check": "Whether a new opcode that a scheduled or proposed fork defines (CLZ 0x1e under Karst, or any byte undefined at Prague) appears outside push data in the deployed PoolManager runtime, which would change what an existing JUMP target or fall-through executes once the fork ships.",
   "result": "Decoding the 24,009 byte runtime from both endpoints with push data skipped finds no opcode byte that is undefined at Prague, so no instruction of the deployed code changes meaning when CLZ or another new opcode activates. The code hashes equal state/networks.json.",
   "source": FORNO + " and " + XL + " eth_getCode; " + WD + "out/code-42220.json, out/code-196.json"},
  {"chainIds": [42220], "lens": "L1",
   "check": "Karst on Celo assumed shipped within six months: the EIP-7825 per transaction gas cap of 16,777,216 against the PoolManager paths other users need to leave a pool.",
   "result": "Liquidity removal touches two ticks, the bitmap words of those ticks and one position (" + src_pool + ":146-204), with no loop over other users' data, so its gas does not grow with what an attacker adds. The only loop is the swap loop (" + src_pool + ":344), which a swapper bounds with its own price limit. A cap can make one very wide swap need several transactions; it cannot block a withdrawal. Karst has no Celo activation time (configs.json) and the roadmap still says Q4 2026 pending readiness.",
   "source": "https://docs.optimism.io/notices/archive/upgrade-19; https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528; " + src_pool + ":146-204, 344"},
  {"chainIds": [42220, 196], "lens": "L5",
   "check": "Owner, protocol fee controller and runtime bytecode reread on 2026-11-27.",
   "result": "Unchanged from cycle 34 and state/networks.json on both networks: owner 0x044a...b6b7 with the same 1,488 byte code, controller zero, runtime hashes as recorded.",
   "source": FORNO + " and " + XL + " eth_call and eth_getCode; " + WD + "out/l5.txt"},
 ],
 "leads": [],
 "leadResults": [
  {"leadId": "L-1305", "outcome": "cleared",
   "answer": "Cycle 36 showed the 24 non-EXP arithmetic handlers are one code body across the six tables and the EXP variants differ only in a gas offset, so table selection cannot change an arithmetic word. Which table block building selects, and whether the unpublished sequencer build is the same binary, cannot be read from outside. At the result level the sequencer's output was checked: the %d swaps mined in blocks %s to %s satisfy the exact tick relation and %d pairs match the single-step formulas of the source, as did 195 swaps in cycle 36. A sequencer build that differs only in rare operand shapes the pools never reach would still not be seen; that residue belongs with L-1203." % (X['swaps'], fmt(X['blocks'][0]), fmt(X['blocks'][1]), X['pairs'])},
  {"leadId": "L-1306", "outcome": "inconclusive" if (remaining or oc['notConverged'] or oc['differ']) else "cleared",
   "answer": rep_text + " A second receipt endpoint (rpc.ankr.com/celo) was set through RCPT_URLS."},
 ],
}
if remaining or oc['notConverged'] or oc['differ']:
    research['leads'].append({"chainIds": [42220], "lens": "L2",
        "question": "Run the Celo parent-storage replay over the %d transactions left in cycles/038/op-stack-custom-gas.work/replay/lwindow-rest.json (gdrive.py skips those already in lazy_*.jsonl), and rerun with a higher MAXR the %d that did not converge (%s)." % (remaining, oc['notConverged'], ', '.join(t[:12] for t in differ) or 'none'),
        "why": "The window is still not closed; each transaction takes about one to five minutes on forno.", "priority": "low"})
json.dump(research, open(NR + '/cycles/038/op-stack-custom-gas.research.json', 'w'), indent=1)
print(json.dumps(summary))
