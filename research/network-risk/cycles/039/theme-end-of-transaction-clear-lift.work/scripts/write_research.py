"""Cycle 39, theme-end-of-transaction-clear-lift: writes the research file from the outputs in ../out."""
import json, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = '/home/user/v4-core/research/network-risk/cycles/039/theme-end-of-transaction-clear-lift.research.json'
WR = 'research/network-risk/cycles/039/theme-end-of-transaction-clear-lift.work'
S = json.load(open(os.path.join(W, 'out', 'summary.json')))
live = {r['chainId']: r for r in json.load(open(os.path.join(W, 'out', 'live-sim.json')))}
for f in ('live-sim-alt-480-480.rpc.thirdweb.com.json', 'live-sim-alt-42220-celo-json-rpc.stakely.io.json', 'live-sim-alt-196-xlayer.drpc.org.json'):
    for r in json.load(open(os.path.join(W, 'out', f))): live[r['chainId']] = r
ALL = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
m = S['main']; fl = S['faults']

BUILDS = [
    ('opreth2100', 'op-reth v2.10.0-rc.4', [130, 57073, 1868, 10], 'discard_tx 0x2d06750 and 0x44f07d0, commit_tx 0x2d08b50 and 0x44f0bd0'),
    ('opreth281', 'op-reth v2.8.1', [10], 'discard_tx 0x2eada10 and 0x4682200, commit_tx 0x2eafe10 and 0x4682600'),
    ('base156', 'Base v1.5.6', [8453], 'discard_tx 0x35bdab0, 0x6432720 and 0x722d500, commit_tx 0x35c17f0, 0x64313d0 and 0x722d180'),
    ('wc282', 'world-chain v2.8.2', [480], 'discard_tx 0x2daf270 and 0x46d9040, commit_tx 0x2db17b0 and 0x46d9440 (named so in the symbol table)'),
    ('conduit251', 'conduit-op-reth v2.5.1', [7777777], 'discard_tx 0x1e34850 and 0x3b85ab0, commit_tx 0x1e37820 and 0x3b85eb0 (named so in the symbol table)'),
    ('xlayer0073', 'xlayer-reth v0.0.7.3-rc.1', [196], 'discard_tx 0x383ba70 and 0x509e360, commit_tx 0x3840de0 and 0x50a0a20'),
    ('arc086', 'arc-execution v0.8.6', [5042], 'discard_tx 0x19f9150, commit_tx 0x1a07a80'),
]

cleared = []
cleared.append(dict(
    chainIds=[130, 57073, 1868, 10, 8453, 480, 7777777, 196, 5042], lens='L1',
    check='Task 1 static pass (L-1323): where the seven builds end a transaction. Cycle 38 looked for the clear inlined into the block executor with the Celo pattern (inc of a 64-bit id next to the depth store) and found none on these builds. This cycle anchored on the id itself.',
    result=('The six builds on revm-state 43 (op-reth v2.10.0-rc.4 and v2.8.1, Base v1.5.6, world-chain v2.8.2, conduit-op-reth v2.5.1, xlayer-reth v0.0.7.3-rc.1) keep TransactionId as a NonMaxU32, stored as id XOR 0xffffffff, so the increment is a load, a dec, a jump to the panic "transaction id overflow" when the result is zero, and a 32-bit store (revm-state-43.0.1/src/lib.rs:61-66). '
            'Every RIP-relative load of that panic message in each binary was found (4 in each build, 6 in Base) and each one sits in an out-of-line JournalInner::commit_tx or discard_tx; none is inlined into the executor, the payload builder or the RPC path. world-chain and conduit-op-reth carry symbols that name these functions. Arc (revm-context 16.0.1, a usize id) has one commit_tx 0x1a07a80 and one discard_tx 0x19f9150, also out of line; the third candidate 0x1b62b30 is a BTreeMap length counter. '
            'Direct callers: 13 to 66 call sites per function; in world-chain every caller is an OpHandler execution_result or catch_error. The layout in all seven builds is the one the frame code uses: transient map at J+0xf0, depth J+0x118, journal length J+0x28, logs J+0x10, third list J+0x40, access list J+0x70, coinbase flag J+0xb0, id J+0x120, with J the journal argument. Routines per build: '
            + '; '.join('%s: %s' % (b[1], b[3]) for b in BUILDS) + '.'),
    source=WR + '/scripts/txpanic.py, out/txpanic-*.json, out/callers-*.json, scripts/txscan_loose.py; dl/src/revm-state-43.0.1/src/lib.rs:61-66 (https://static.crates.io/crates/revm-state/revm-state-43.0.1.crate, sha256 3b2d2ec0... equal to the crates.io checksum)'))
for prof, name, cids, fns in BUILDS:
    t = m[prof]; f = fl[prof]
    cleared.append(dict(
        chainIds=cids, lens='L1',
        check='Task 1 dynamic run of the end-of-transaction routines of %s from the binary (%s): %d populated journal states over %d routines, seeds 39001 and up per routine (out/units.txt), in the cycle 27-38 x86-64 model (objdump text interpreted, nothing executed or loaded).' % (name, fns, t['cases'], t['fns']),
        result=('Every state held the PoolManager lock word, the nonzero delta count, three currency delta words, the synced currency and reserves words and up to nine more transient words (%d words in all), storage writes in nested frames with frames left open in %d states (depth up to %d, journal up to %d entries), %d logs with allocated topics, %d access list entries and the coinbase flag. '
                'After each routine the transient map held no item and every control byte was EMPTY, every written transient word read zero through the lifted TLOAD, the depth was 0, the journal, logs and third list were empty with every topic and key set block freed, the access list was empty, the coinbase flag 0 and the id advanced by one; discard put every slot back at its original value and commit kept every present value; a next transaction wrote and read the lock. No mismatch and no stop. '
                'Task 5: %d of %d planted faults caught (transient map kept, journal kept, depth left raised, id not advanced, logs kept; one of each per routine).') % (t['words'], t['open'], t['maxd'], t['maxj'], t['logs'], t['al'], f[0], f[1]),
        source=WR + '/scripts/txrun39.py, out/main-%s-*.json, out/fault-%s-*.json, out/faults39.json' % (prof, prof)))
t = m['celo1010']; f = fl['celo1010']
cleared.append(dict(
    chainIds=[42220], lens='L1',
    check='Task 3 (L-1350): celo-reth v1.0.10 JournalInner::finalize 0x1d66c80 run from the binary. The call the lead named goes through slot 0x52b8b08 (RELATIVE, target 0x50b23b0); 0x52c0de0 is the GLOB_DAT slot of glibc syscall and no instruction of finalize or of 0x50b23b0 references it.',
    result=('0x50b23b0 is the std RandomState key read for the new empty state map that mem::take leaves: it reads a per-thread flag at fs-0x80 and, when set, returns the thread key at fs-0x88 and increments it; only on a thread\'s first map does it call the initialiser 0x50b23f0, the random-key path. With the flag set, as on any thread that has built a map before, %d populated states ran: the returned state was the old table, the journal state map was empty with the next thread key, the transient map, logs, journal and access list were empty, the coinbase flag 0, depth and id zeroed together by one 16-byte store at 0x1d66fe6, and a next transaction read zero for every written transient word. %d of %d planted faults caught. The initialiser itself was not run.') % (t['cases'], f[0], f[1]),
    source=WR + '/out/main-celo1010-1d66c80.json, out/fault-celo1010-1d66c80-*.json; readelf -r of celo-reth (0x52b8b08 RELATIVE 0x50b23b0, 0x52c0de0 GLOB_DAT syscall)'))
cleared.append(dict(
    chainIds=[130, 57073, 1868, 10, 480], lens='L1',
    check='Task 2: which end-of-transaction routine runs on each path of the OP Stack executor, read in op-revm handler.rs at op-reth/v2.10.0-rc.4 (65e80332, identical file) and at 7220729 (world-chain v2.8.2 build path), alloy-op-evm lib.rs, op-revm api/exec.rs and revm-handler 43.0.3.',
    result=('A user transaction that succeeds, reverts or halts ends in execution_result, which calls commit_tx (handler.rs:408-433). A transaction rejected in validation or pre-execution (nonce, balance for the L1 fee) or by a database error ends in catch_error, which calls discard_tx (handler.rs:440-504); Handler::run sends every Err of run_without_catch_error there (revm-handler handler.rs:100-109), including the take_error at the start of execution_result. A deposit that succeeds takes commit_tx; a deposit that fails, or halts after Regolith (HaltedDepositPostRegolith), takes catch_error_failed_deposit: checkpoint_revert to the first checkpoint, nonce bump and mint, then commit_tx (handler.rs:509-535). '
            'Every block transaction goes through OpEvm::transact_raw, which calls revm ExecuteEvm::transact or inspect_tx (alloy-op-evm lib.rs:386-405); transact is transact_one followed by finalize (revm-handler api.rs:72-80), and OpEvm::finalize is JournalInner::finalize (op-revm api/exec.rs:77-78), a second clear of the transient map, journal, depth and id. So each path clears twice. The two handler files differ only in comments and one cast. In world-chain v2.8.2 every caller of commit_tx and discard_tx is an OpHandler execution_result or catch_error.'),
    source='https://raw.githubusercontent.com/ethereum-optimism/optimism/65e80332/rust/op-revm/src/handler.rs'))
cleared.append(dict(
    chainIds=[1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 4217], lens='L1',
    check='Task 5 live: one eth_simulateV1 block per network of seven transactions (helper and token code by state override, nothing sent): a control that syncs and reads the synced words in one transaction, a successful sync by an ordinary account that leaves CURRENCY_SLOT and RESERVES_OF_SLOT set at its end, a read, a helper that syncs and reverts at the end, a read, a sync from the OP Stack depositor address 0xdead...0001, a read. Each read takes LOCK, NONZERO_DELTA_COUNT, CURRENCY, RESERVES_OF and three delta words with exttload(bytes32[]). Bracketed with web3_clientVersion.',
    result='On all 16 networks whose endpoints serve the method the control returned the mock currency and 0x1234 and every read returned seven zero words: ' + '; '.join(
        '%d %s' % (c, live[c].get('client_before')) for c in [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 4217]) +
        '. World Chain answered through 480.rpc.thirdweb.com, Celo through celo-json-rpc.stakely.io, X Layer through xlayer.drpc.org, because the listed endpoints refuse the method (HTTP 401 "Only core evm requests are allowed" and HTTP 403 "rpc method is not whitelisted"). Avalanche, Monad, MegaETH, Arc and HyperEVM answer that the method does not exist. The depositor call is an ordinary call in the simulator; no endpoint was offered a type 0x7e transaction.',
    source=WR + '/scripts/live_sim.py, out/live-sim.json, out/live-sim-alt-*.json'))
cleared.append(dict(
    chainIds=[42161, 4663, 99901, 137, 56, 43114, 143, 999], lens='L1',
    check='Scope of this theme by client.',
    result='The theme reads the end-of-transaction code of reth-derived clients. Arbitrum One, Robinhood Chain and Elysium (Nitro), Polygon (bor), BNB Chain (the endpoint answers Geth v1.8.2), Avalanche (avalanchego) and Monad run no reth-derived client, so the theme does not apply to them; their transient clear is go-ethereum or Monad code read in other units. HyperEVM\'s validator is closed and is not covered here.',
    source=WR + '/out/live-sim.json (web3_clientVersion of each endpoint)'))
cleared.append(dict(
    chainIds=ALL, lens='L1',
    check='What a leaked word would do in src/, so the runs above test the right thing.',
    result='sync is callable without unlock and leaves CURRENCY_SLOT and RESERVES_OF_SLOT set at the end of a successful transaction (src/PoolManager.sol:279-288, src/libraries/CurrencyReserves.sol:27-32); _settle pays balanceOf minus the stored reserves to whoever settles next (src/PoolManager.sol:349-364). A word carried into the next transaction would let its settler be credited with tokens another user sent in between; a carried lock or count would let take or mint run outside unlock (src/libraries/Lock.sol:10-27, src/libraries/NonzeroDeltaCount.sol:12-33, src/PoolManager.sol:104-114). These are exactly the words the binary runs and the live reads checked; none survives on any build or endpoint tested.',
    source='src/PoolManager.sol:279-288'))

leads = [
    dict(chainIds=[130, 57073, 1868, 10, 8453, 480, 7777777, 196, 5042], lens='L1',
         question='Run the inlined JournalInner::finalize copies of the six revm-state 43 builds and of Arc (candidate sites that store 0xffffffff, the NonMaxU32 zero, to the id word next to a depth store: 5 to 7 per revm-state 43 binary in out/txscan2-*.json; the usize copies of Arc are not located) from the binaries.',
         why='finalize is the second clear after every block transaction; only the commit and discard routines ran here, and only Celo\'s finalize.', priority='low'),
    dict(chainIds=[8453], lens='L1',
         question='Read Base v1.5.6\'s own handler source (revm-handler 42.0.1, alloy-evm 0.38.0, no op-revm path string in the binary) and map each transaction path to its commit or discard caller.',
         why='Task 2 was read from op-revm source for op-reth and world-chain; Base\'s routines ran from the binary but its path mapping is unread.', priority='low'),
    dict(chainIds=[480], lens='L1',
         question='Read the world-chain v2.8.2 payload builder for priority blockspace transactions and for transactions executed speculatively and dropped, and say which evm entry point they use.',
         why='The binary shows only OpHandler callers of commit_tx and discard_tx, but the builder source was not read.', priority='low'),
    dict(chainIds=[5042, 4326, 143, 999, 43114], lens='L1',
         question='Find a public endpoint for Arc, MegaETH, Monad, HyperEVM or Avalanche that serves eth_simulateV1 or another multi-transaction call, and repeat the seven-transaction block.',
         why='Their listed endpoints do not serve the method, so the live cross-transaction read is missing there.', priority='low'),
]
leadResults = [
    dict(leadId='L-1323', outcome='cleared', answer='The premise that the seven builds inline the clear was wrong: on all seven the end-of-transaction routines are out-of-line commit_tx and discard_tx (the earlier search missed them because six builds store the id as a NonMaxU32 and increment it with dec). All 28 routines ran from the binaries on %d populated states with no mismatch, and all %d planted faults were caught.' % (sum(m[p]['cases'] for p in m if p != 'celo1010'), sum(fl[p][1] for p in fl if p != 'celo1010'))),
    dict(leadId='L-1350', outcome='cleared', answer='finalize 0x1d66c80 calls slot 0x52b8b08 (std RandomState key read 0x50b23b0); 0x52c0de0 is glibc syscall and is not referenced by finalize. With the per-thread key flag set, %d populated states cleared fully and %d of %d faults were caught.' % (m['celo1010']['cases'], fl['celo1010'][0], fl['celo1010'][1])),
    dict(leadId='L-1322', outcome='inconclusive', answer='Read in revm-database 43.0.1 only (src/states/state.rs:350-365, https://static.crates.io/crates/revm-database/revm-database-43.0.1.crate, checksum equal to crates.io): when a block access list is set with set_bal, a value it holds is returned in place of the database value, so the PoolManager would read the list\'s value. The list is set by the block executor from the block being executed, which an ordinary account cannot write; the branch 0x477cda1 was not run from the binary and the callers of set_bal in op-reth were not read.'),
]
out = dict(unit='theme-end-of-transaction-clear-lift', profiles=[], findings=[], cleared=cleared, leads=leads, leadResults=leadResults)
json.dump(out, open(R, 'w'), indent=1)
print('written', R, len(cleared), 'cleared', len(leads), 'leads')
