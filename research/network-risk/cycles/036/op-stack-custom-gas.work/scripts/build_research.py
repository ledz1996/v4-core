"""Cycle 36: write op-stack-custom-gas.research.json from the outputs in out/ and replay/."""
import json, glob, collections
W = '/home/user/v4-core/research/network-risk/cycles/036/op-stack-custom-gas.work'
OUT = '/home/user/v4-core/research/network-risk/cycles/036/op-stack-custom-gas.research.json'
WD = 'cycles/036/op-stack-custom-gas.work/'
FORNO = 'https://forno.celo.org'; XL = 'https://rpc.xlayer.tech'; STK = 'https://celo-json-rpc.stakely.io'
IMG = 'cycles/035/theme-reth-keccak-asm-image-lift.work/dl/'


def arith(pat):
    t = collections.Counter(); by = {}
    for f in sorted(glob.glob(W + '/out/' + pat)):
        d = json.load(open(f))
        for k in ('cases', 'mismatches', 'errors'): t[k] += d[k]
        for op, v in d['byOp'].items():
            b = by.setdefault(op, [0, 0, 0])
            for j in range(3): b[j] += v[j]
    return t, by


ca, cby = arith('arith-celo-a-[0-9].json')
xa, xby = arith('arith-xl-a-[0-9].json')
xsx, _ = arith('arith-xl-a-sx.json')
exps = {n: arith('arith-%s-exp.json' % n)[0] for n in ('xl-b', 'xl-c', 'celo-b', 'celo-c', 'celo-d')}
assert ca['mismatches'] == ca['errors'] == 0 and xa['mismatches'] == 0 and xsx['mismatches'] == xsx['errors'] == 0
assert all(e['mismatches'] == e['errors'] == 0 for e in exps.values())
# X Layer main run: the only errors are SIGNEXTEND cases stopped at pinsrw before the model had that instruction
assert xa['errors'] == xby['SIGNEXTEND'][2]
faults = {}
for f in glob.glob(W + '/out/arith-*-fault-*.json'):
    d = json.load(open(f)); faults[f.split('/')[-1][6:-5]] = d['mismatches'] + d['errors']
jd = {n: json.load(open(W + '/out/jd-%s.json' % n)) for n in ('celo', 'xl')}
jdf = {f.split('/')[-1][3:-5]: (lambda d: d['mismatches'] + d['errors'])(json.load(open(f))) for f in glob.glob(W + '/out/jd-*-fault-*.json')}
assert all(jd[n]['mismatches'] == jd[n]['errors'] == 0 for n in jd)

# replay (L-1067)
recs = {}
for f in sorted(glob.glob(W + '/replay/lazy_*.jsonl')) + sorted(glob.glob(W + '/replay/rerun_*.jsonl')):
    for l in open(f):
        try: r = json.loads(l)
        except ValueError: continue
        if r['tx'] not in recs or 'error' in recs[r['tx']]: recs[r['tx']] = r
oc = collections.Counter(); pmlogs = slots = native = ct = 0
for r in recs.values():
    if r.get('error'): oc['infra'] += 1; continue
    ct += r.get('celoTransfers') or 0
    if r.get('match'): oc['match'] += 1; pmlogs += r.get('pmLogs') or 0; slots += r.get('pmSlotsCompared') or 0; continue
    p = r.get('prefix')
    if isinstance(p, dict) and p.get('match'): oc['prefix'] += 1; pmlogs += p.get('pmLogs') or 0; slots += p.get('pmSlotsCompared') or 0; continue
    pm_ok = r.get('statusChain') == r.get('statusRef') and r.get('pmLogsEqual') and not r.get('pmSlotMismatch') and r.get('pmNativeEqual') is not False
    if pm_ok: oc['otherlogs'] += 1; continue
    oc['open'] += 1
rep = dict(oc); rep['n'] = len(recs); rep['celoTransfers'] = ct; rep['pmSlots'] = slots; rep['pmLogs'] = pmlogs
json.dump(rep, open(W + '/replay/summary.json', 'w'), indent=1)
print('replay', rep)

fmt = lambda n: '{:,}'.format(n)
d = {"unit": "op-stack-custom-gas", "_lenses": ["L1", "L2", "L4", "L6"], "profiles": [], "findings": [], "cleared": [], "leads": [], "leadResults": []}
P = d["profiles"]
P.append({"chainId": 42220, "lens": "L1",
  "summary": "First run of the shipped celo-reth arithmetic and jump analysis code. The 25 arithmetic, comparison and shift handlers of the celo-reth v1.0.10 image (reth 74cc8bb, the build forno and stakely answer), with the 11 ruint and i256 routines they reach, gave the specified word on all %s cases in the x86-64 model, and its analyze_legacy gave the specified bitmap and padding on 510 programs. The image lays its instruction table out differently from every reth build lifted before." % fmt(ca['cases']),
  "deltas": [
    {"delta": "The celo-reth v1.0.10 image (usr/local/bin/celo-reth, sha256 prefix ca81b8701ff8bb3b, built from reth checkout 74cc8bb, the celo-org/revm checkout bd28f94 and ruint 1.20.0 by the paths it embeds) keeps 20 instruction tables of 256 entries of 16 bytes (handler and static gas) at 0x5142468 and following, where the op-reth, Base, conduit and World Chain builds lifted in cycles 32 and 35 use 8 byte entries. Handlers return nothing and halt by a tail call through the GOT to halt_underflow, halt_not_activated or halt (0x35f4750 to 0x35f47e0). All tables share one handler per opcode except EXP, which has four copies reading the byte cost through host offsets 0x378 (three) and 0x2c8 (one). No earlier cycle had run this code.", "source": IMG + "celo-v1.0.10/x/usr/local/bin/celo-reth read with objdump and readelf; " + WD + "build/celo-arith.json, out/tabs-celo.json", "relevance": "low"},
    {"delta": "Run in the cycle 32 x86-64 model (copied with one added instruction, pinsrw, which SIGNEXTEND uses): table 0x5142468 gave the reference word on %s of %s cases (battery, targeted, maxmod, maxmod2 and v4math sets: MULMOD %s, ADDMOD %s, DIV %s, MOD %s, SHL %s, SHR and SAR %s each, SIGNEXTEND %s), 0 errors; the other three EXP copies gave 652 of 652 each. Planted faults in mul_mod_by_ref (a dropped carry at 0x35873ee) and in SHL (the 128 bit select at 0x1e70c15) were caught at the 20 case limit. A first SHL fault, the 256 bound at 0x1e70b6f, was not observable because the branch-free code below it also yields zero for a shift of 256." % (fmt(ca['cases'] - ca['mismatches']), fmt(ca['cases']), fmt(cby['MULMOD'][0]), fmt(cby['ADDMOD'][0]), fmt(cby['DIV'][0]), fmt(cby['MOD'][0]), fmt(cby['SHL'][0]), fmt(cby['SHR'][0]), fmt(cby['SIGNEXTEND'][0])), "source": WD + "out/arith-celo-a-0.json to -2.json, arith-celo-{b,c,d}-exp.json, arith-celo-a-fault-*.json; scripts/arith.py, x86emu2.py", "relevance": "low"},
    {"delta": "analyze_legacy at 0x4fc6fa0 (1,113 bytes, frame-pointer build, text differs from Base's revm-bytecode build) with its 8 callees, run in the model on the PoolManager runtime, 60 prefixes, 32 trailing PUSH cases, 16 last-byte cases, the empty code and 400 random programs: 510 of 510 equal the specification and the crate padding; the PoolManager has 610 valid JUMPDEST and 29 0x5b bytes inside push data, all excluded. Planted faults at the JUMPDEST compare and the PUSH bound were caught.", "source": WD + "out/jd-celo.json, jd-celo-fault-*.json; build/celo.jd.json", "relevance": "low"},
    {"delta": "celo-json-rpc.stakely.io answered reth/v2.2.0-74cc8bb to 6 of 6 web3_clientVersion calls (cycle 34 saw 7680d6d and 3cbf835); forno answered 74cc8bb 5 times and the op-geth c7ed55b8 build of F-116 once. No celo-kona tag after celo/reth-v1.0.10 (20 November 2026).", "source": FORNO + "; " + STK + " (" + WD + "out/clientver.txt); https://github.com/celo-org/celo-kona/tags", "relevance": "none"}]})
P.append({"chainId": 42220, "lens": "L2",
  "summary": "The parent-storage replay of L-1067 was extended past transaction 2,479 of the cycle 24 Celo window by %d transactions; none differs from the chain in a PoolManager log, PoolManager storage word or native balance." % (rep['n'] - rep.get('infra', 0)),
  "deltas": [{"delta": "Of %d transactions from window positions 2,480 onward (blocks 79,574,208 to 80,191,320), %d match outright, %d match after their block prefix, %d differ only in logs of other contracts with PoolManager status, logs, words and balance equal, and %d could not run because no endpoint served a receipt. %s PoolManager storage words and %d CELO transfer precompile calls were compared or modelled." % (rep['n'], rep.get('match', 0), rep.get('prefix', 0), rep.get('otherlogs', 0), rep.get('infra', 0), fmt(rep['pmSlots']), rep['celoTransfers']), "source": FORNO + " and https://rpc.ankr.com/celo (eth_getStorageAt, eth_getCode, eth_getBalance, receipts), " + WD + "replay/summary.json, lazy_*.jsonl, rerun_*.jsonl", "relevance": "none"}]})
P.append({"chainId": 42220, "lens": "L4",
  "summary": "Nothing new among the special addresses the PoolManager can reach. Karst, which would add the L2 Contract Manager route for predeploy upgrades, is not scheduled on Celo.", "deltas": []})
P.append({"chainId": 42220, "lens": "L6",
  "summary": "No Celo network upgrade has an activation time in the next six months. Karst is targeted at the fourth quarter of 2026 without a date, Lagoon is not scheduled for Celo, and Espresso confirmations run only on a devnet.",
  "deltas": [
    {"delta": "The mainnet entry for chain 42220 in celo-kona main crates/kona/registry/etc/configs.json lists hardfork times up to jovian_time 1774958788 and no karst_time; docs.celo.org lists no active upgrade notice (only the op-geth end of support and the req/resp sync deprecation).", "source": "https://raw.githubusercontent.com/celo-org/celo-kona/main/crates/kona/registry/etc/configs.json; https://docs.celo.org/llms.txt", "relevance": "low"},
    {"delta": "The Celo Core Co. H2 2026 roadmap says Karst is to be prepared and activated in Q4 pending readiness, with governance tooling, execution changes and Kona proofs; upstream Karst (OP Upgrade 19) brings EIP-7825, CLZ, MODEXP and P256VERIFY repricing, the bn256 pairing input cap and the L2 Contract Manager.", "source": "https://forum.celo.org/t/h1-2026-engineering-retro-h2-2026-roadmap/13528; https://docs.optimism.io/notices/archive/upgrade-19", "relevance": "low"},
    {"delta": "Lagoon (OP Upgrade 22: BLS12-381 input limits, post-execution transaction type 0x7D, sequencer defined metering, interop) has no superchain default; each chain sets its own time, and only OP Mainnet, Unichain, Ink and Soneium are listed (11 January 2027). Espresso lists Celo only as an unstable devnet.", "source": "https://docs.optimism.io/op-stack/protocol/hardforks/lagoon; https://docs.optimism.io/notices/upgrade-22; https://docs.espressosys.com/network/llms-full.txt", "relevance": "none"}]})
P.append({"chainId": 196, "lens": "L1",
  "summary": "First run of the shipped X Layer arithmetic and jump analysis code. The xlayer-reth v0.0.7.3-rc.1 image (okx/reth f60420a, the build rpc.xlayer.tech answers; revm-interpreter 37.0.3, revm-bytecode 11.0.1, ruint 1.18.0) carries six instruction tables whose 24 non-EXP handlers have one normalised code body, different from every reth build lifted before; all %s cases gave the specified word in the x86-64 model and analyze_legacy matched on 510 programs." % fmt(xa['cases']),
  "deltas": [
    {"delta": "The image binary usr/local/bin/op-reth (sha256 prefix 7a9230ac67a539a1) has six 8 byte entry tables (0x70cb168, 0x70cc968, 0x718b9e0, 0x718f1e0, 0x71909e0, 0x71919e0) in two code copies (handlers at 0x3d2e... and 0x5deb...). Compared as normalised text with every direct, tail and GOT callee, the 24 handlers other than EXP are identical across all six tables, and EXP has three variants that differ only in the host offset of the byte cost (0x5c0, 0x450, 0x490). Against op-reth v2.10.0-rc.4, conduit-op-reth v2.5.1 and Base v1.5.6 only NOT is identical, so no earlier lift covered this code.", "source": IMG + "xlayer-rc1/x/usr/local/bin/op-reth read with objdump and readelf; " + WD + "out/hcmp-xl.json, tabs-xl.json; scripts/hcmp.py, findtab.py", "relevance": "low"},
    {"delta": "In the model, table 0x70cb168 gave the reference word on %s of %s cases with 0 mismatches; the %s SIGNEXTEND cases that stopped at pinsrw before the model had that instruction were rerun and all %s match. The EXP variants of 0x70cc968 and 0x718f1e0 gave 652 of 652 each. SHL bounds its amount on the full word (upper limbs zero and low limb below 0x100) before any shift, so ruint's wrapping_shl is never reached with a large amount. Planted faults (SHL bound 0x3d2f759, mul_mod carry 0x3bfc9ed) were caught." % (fmt(xa['cases'] - xa['errors']), fmt(xa['cases']), fmt(xa['errors']), fmt(xsx['cases'])), "source": WD + "out/arith-xl-a-0.json to -3.json, arith-xl-a-sx.json, arith-xl-{b,c}-exp.json, arith-xl-a-fault-*.json", "relevance": "low"},
    {"delta": "The jump destination analysis loop at 0x40da4b0 (1,253 bytes, the only function in the binary with the PUSH step and JUMPDEST compare pattern) with its three callees gave 510 of 510 programs equal to the specification and the crate padding; the PoolManager has 610 valid JUMPDEST. Planted faults were caught.", "source": WD + "out/jd-xl.json, jd-xl-fault-*.json; scripts/findjd.py; build/xl.jd.json", "relevance": "low"},
    {"delta": "rpc.xlayer.tech answered reth/v2.3.0-f60420a/x86_64-unknown-linux-gnu/xlayer/v0.0.7 to 6 of 6 calls. No xlayer-reth tag after v0.0.7.3-rc.1 (5 November 2026). The v0.0.7.3 release note says the code is in sync with reth v2.3.0 through okx/reth 81573d2, while the binary and the endpoint name f60420a.", "source": XL + " (" + WD + "out/clientver.txt); https://github.com/okx/xlayer-reth/tags; https://github.com/okx/xlayer-reth/releases", "relevance": "none"}]})
P.append({"chainId": 196, "lens": "L2", "summary": "Nothing new on transaction boundaries or state changes outside the EVM this cycle.", "deltas": []})
P.append({"chainId": 196, "lens": "L4",
  "summary": "The op-node release paired with xlayer-reth v0.0.7.3 adds a GASLESS_WHITELIST predeploy for the gasless path that F-151 records; it governs fee waivers and holds no pool funds.",
  "deltas": [{"delta": "okx/optimism xlayer/v0.1.7 adds the Gasless whitelist contract and the GASLESS_WHITELIST predeploy and ports gasless execution to the Rust stack, with a fix so the base fee bypass applies only to the intended transaction.", "source": "https://newreleases.io/project/github/okx/optimism/release/xlayer%2Fv0.1.7", "relevance": "low"}]})
P.append({"chainId": 196, "lens": "L6",
  "summary": "No X Layer upgrade is scheduled. The xlayer-reth chainspec on main ends at Jovian, and the status page lists nothing after the 10 November 2026 mainnet hard fork.",
  "deltas": [{"delta": "crates/chainspec/src/lib.rs on xlayer-reth main sets XLAYER_MAINNET_JOVIAN_TIMESTAMP 1764691201 as the last fork condition and has no Karst or Lagoon entry.", "source": "https://raw.githubusercontent.com/okx/xlayer-reth/main/crates/chainspec/src/lib.rs; https://status.xlayer.tech/maintenance", "relevance": "none"}]})

C = d["cleared"]
C.append({"chainIds": [42220], "lens": "L1", "check": "Arithmetic, comparison and shift handlers of the shipped celo-reth v1.0.10 image (16 byte table entries, void handlers, ruint 1.20.0 mul_mod_by_ref, div_rem_by_ref, div_rem_bits_plus_one, add_mod, wrapping_pow, i256_div and i256_mod) run in the x86-64 model on the inputs that decide FullMath.mulDiv (src/libraries/FullMath.sol:24, :48, :112), TickMath (src/libraries/TickMath.sol:63, :80, :104, :111, :142-144), BitMath (src/libraries/BitMath.sol:16-19) and TickBitmap (src/libraries/TickBitmap.sol:20-26, :38).",
  "result": "%s of %s cases give the reference word, 0 errors, plus 652 of 652 for each of the three other EXP copies. A wrong MULMOD would change the high half rebuilt at FullMath.sol:24; a wrong SDIV or SMOD would put negative ticks in the wrong word at TickBitmap.sol:24-26; neither occurs. Planted faults are caught." % (fmt(ca['cases']), fmt(ca['cases'])),
  "source": WD + "out/arith-celo-a-*.json, arith-celo-*-exp.json, arith-celo-a-fault-*.json; " + IMG + "celo-v1.0.10/x/usr/local/bin/celo-reth"})
C.append({"chainIds": [196], "lens": "L1", "check": "Arithmetic, comparison and shift handlers of the shipped xlayer-reth v0.0.7.3-rc.1 image (six tables, one non-EXP code body, three EXP variants, ruint 1.18.0) run in the x86-64 model on the same inputs.",
  "result": "%s cases with 0 mismatches (SIGNEXTEND rerun: %s of %s), 652 of 652 for each further EXP variant. Planted faults are caught. Because all six tables share one code body per opcode, the sequencer and followers run the same arithmetic whichever table their EVM configuration selects." % (fmt(xa['cases']), fmt(xsx['cases']), fmt(xsx['cases'])),
  "source": WD + "out/arith-xl-a-*.json, arith-xl-*-exp.json, hcmp-xl.json; " + IMG + "xlayer-rc1/x/usr/local/bin/op-reth"})
C.append({"chainIds": [42220, 196], "lens": "L1", "check": "Legacy jump destination analysis of both images (Celo analyze_legacy 0x4fc6fa0, X Layer 0x40da4b0) on the PoolManager runtime and 509 other programs, as it decides which JUMP and JUMPI targets of the PoolManager are valid.",
  "result": "510 of 510 per image equal the specification and the crate padding; 610 JUMPDEST accepted, the 29 0x5b bytes in push data rejected. Planted faults at the JUMPDEST compare and the PUSH bound are caught on both.",
  "source": WD + "out/jd-celo.json, jd-xl.json, jd-*-fault-*.json"})
C.append({"chainIds": [42220, 196], "lens": "L1", "check": "Reruns of battery.py, targeted.py, pmdiff.py, pmdiff2.py, swaps.py and replay.py for 42220 and 196 on forno.celo.org and rpc.xlayer.tech.",
  "result": "185,529 of 185,529 vectors, 250 of 250 and 300 of 300 scripts identical to Ethereum on both. Mined swaps: Celo 129 and X Layer 195 satisfy the tick relation; of the pairs, Celo 90 and X Layer 170 match the single-step formulas, and the 9 Celo multi-step swaps replay to the unit (up to 26 steps).",
  "source": WD + "out/battery.log, targeted.log, pmdiff.log, pmdiff2.log, swaps.json, replay.json; eth_call with state override on " + FORNO + " and " + XL})
C.append({"chainIds": [42220, 196], "lens": "L1", "check": "ruint fixes after the pinned versions (1.20.0 on Celo, 1.18.0 on X Layer): PR 603 (1.20.0) says the LIMBS 1, 2 and 4 fast paths of wrapping_shl and wrapping_shr cast the amount to u32, so amounts of 2^32 or more wrapped; PR 666 (1.21.0) fixes div_3x2_ref.",
  "result": "No EVM result changes. The lifted SHL, SHR and SAR handlers of both images test the whole amount word before shifting and return zero or the sign fill for 256 or more, so the wrapping fast path never sees a large amount; the battery's shift vectors with amounts up to 2^256-1 pass in the model and on both endpoints. PR 666 says the library's division uses div_3x2_mg10, so only direct callers of div_3x2_ref change. TickMath.sol:63, :111 and TickBitmap.sol:38 shift by constants below 256.",
  "source": "https://raw.githubusercontent.com/recmo/uint/main/CHANGELOG.md; https://github.com/alloy-rs/ruint/pull/603; https://github.com/alloy-rs/ruint/pull/666; " + WD + "build/celo-arith.s (0x1e70b20), build/xl-arith.s (0x3d2f710)"})
C.append({"chainIds": [42220, 196], "lens": "L6", "check": "Upgrades in the next six months assumed shipped: Karst on Celo (Q4 2026 target) and on X Layer (not scheduled), and Lagoon if either adopts it.",
  "result": "Nothing new for funds in the PoolManager. Karst effects were cleared in cycles 15 and 20 (CLZ is not an instruction of the deployed bytecode; the 16,777,216 gas cap leaves exits possible); its L2 Contract Manager is a governance route already counted in F-026 and F-140. Lagoon's BLS12-381 limits only bound precompiles the PoolManager reaches with empty calldata through a caller-chosen native payout (P1), and its 0x7D post-execution transaction is appended by the sequencer to rebate gas, which an ordinary account cannot send.",
  "source": "https://docs.optimism.io/notices/archive/upgrade-19; https://docs.optimism.io/notices/upgrade-22; https://specs.optimism.io/protocol/lagoon/exec-engine.html; src/types/Currency.sol:44-52"})

L = d["leads"]
L.append({"chainIds": [42220, 196], "lens": "L2", "question": "Do the SLOAD, SSTORE, TLOAD and TSTORE handlers and the journal checkpoint and revert of the celo-reth v1.0.10 and xlayer-reth v0.0.7.3-rc.1 images, which are on disk and whose handler code differs from every lifted build, give the reference result in the model?", "why": "Cycle 35 lifted the journal of op-reth and Base only. These carry the lock, the delta count and the synced currency that decide src/PoolManager.sol:104-114 and the settle credit at src/PoolManager.sol:349-364.", "priority": "medium"})
L.append({"chainIds": [196], "lens": "L1", "question": "Which of the six instruction tables of the X Layer binary does block building select, and is the unpublished sequencer build the same binary?", "why": "The arithmetic is one code body in all six tables, so only an unpublished sequencer build could differ (L-1203 concerns the same).", "priority": "low"})
L.append({"chainIds": [42220], "lens": "L2", "question": "Run the Celo parent-storage replay over the window positions after the %d transactions of this cycle, with receipts from a second endpoint for the ones forno answers null." % rep['n'], "why": "L-1067 asked for the rest of the Celo window; one replay takes about 10 to 300 seconds, mostly waiting on the endpoint.", "priority": "low"})

d["leadResults"].append({"leadId": "L-1067", "outcome": "inconclusive", "answer": "Celo part only (Zora, World Chain and Soneium belong to the op-stack-eth unit). %d transactions beyond position 2,479 of the cycle 24 window were replayed from parent-block storage with the unchanged cycle 24 gdrive.py: %d match, %d match after their block prefix, %d differ only in logs of other contracts, %d could not run for lack of a served receipt, and none differs in a PoolManager log, storage word or native balance. The rest of the window remains." % (rep['n'], rep.get('match', 0), rep.get('prefix', 0), rep.get('otherlogs', 0), rep.get('infra', 0))})
assert rep.get('open', 0) == 0, rep
json.dump(d, open(OUT, 'w'), indent=1)
print('written', OUT, faults, jdf)
