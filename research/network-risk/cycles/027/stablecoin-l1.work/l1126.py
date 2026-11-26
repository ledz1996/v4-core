"""L-1126: run the long sequences of theme-stateful-interpreter (cycle 26) on Tempo within the 25,000,000 gas its
endpoint grants, and compare every returned word with the reference interpreter (tools/opdiff/pyevm.py).
Read-only: eth_call with state overrides only. Nothing is deployed and nothing is sent.

How the sequences are made to fit. Tempo prices a new storage slot at 250,000 gas (TIP-1000), so the setup steps of
sequence a (32 pools' worth of new slots) and the 300 new ERC-6909 balance slots of d300 use most of the budget.
 - a64: the setup steps are run in the reference interpreter first; their resulting storage (PoolManager, driver and
   token doubles) is handed to the endpoint as stateDiff overrides. Then the swap rounds are run as one call, so all
   rounds still run one after another in one EVM instance and every FullMath.mulDiv sees the same alternating
   denominators as in the original sequence. If all rounds do not fit, the prefix is grown and fewer rounds run.
   The reference is run from exactly the same storage.
 - d300: the 300 ERC-6909 balance slots balanceOf[driver][id] and the driver's output array slots are pre-set to a
   nonzero value by stateDiff in both the endpoint call and the reference, so mint and burn rewrite occupied slots.
   The returned words (deltas, counts) do not read balances, so they are unchanged by the pre-set values.
Usage: python3 -I l1126.py <outdir> [names...]"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
S26 = os.path.abspath(os.path.join(HERE, '..', '..', '026', 'theme-stateful-interpreter.work', 'scripts'))
sys.path.insert(0, S26)
import seqlib as S  # noqa: E402
import pyevm as P  # noqa: E402
from evm import rpc, keccak  # noqa: E402

URL = 'https://rpc.mainnet.tempo.xyz'
PM = 0x33620f62c5b9b2086dd6b62f4a297a9f30347029
GAS = 25_000_000


def world(storage=None):
    wd = P.World(S.codes(PM))
    if storage:
        wd.storage.update(storage)
    return wd


def ref_run(steps, storage=None):
    wd = world(storage)
    ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(steps), False, 0)
    return ok, (S.dec_run(ret) if ok else ret.hex()), dict(wd.storage)


def overrides(storage):
    ov = {}
    for a, c in S.codes(PM).items():
        ov['0x%040x' % a] = {'code': '0x' + c.hex()}
    for (a, k), v in (storage or {}).items():
        e = ov.setdefault('0x%040x' % a, {})
        e.setdefault('stateDiff', {})['0x%064x' % k] = '0x%064x' % v
    return ov


def cv():
    try:
        return rpc(URL, 'web3_clientVersion', [], timeout=30)
    except Exception as e:  # noqa
        return 'error ' + str(e)[:100]


def chain(steps, storage, trace=False):
    rec = {'clientBefore': cv(), 'nsteps': len(steps), 'overrideSlots': len(storage or {})}
    blk = rpc(URL, 'eth_blockNumber', [], timeout=30); rec['block'] = int(blk, 16)
    tx = {'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.D, 'data': '0x' + S.enc_run(steps).hex(), 'gas': hex(GAS)}
    ov = overrides(storage)
    try:
        r = rpc(URL, 'eth_call', [tx, blk, ov], timeout=300)
        rec['steps'] = S.dec_run(bytes.fromhex(r[2:]))
    except Exception as e:  # noqa
        rec['error'] = str(e)[:400]
    if trace:
        try:
            t = rpc(URL, 'debug_traceCall', [tx, blk, {'tracer': 'callTracer', 'tracerConfig': {'onlyTopCall': True},
                                                       'stateOverrides': ov}], timeout=300)
            rec['gasUsed'] = int(t.get('gasUsed', '0x0'), 16)
        except Exception as e:  # noqa
            rec['traceError'] = str(e)[:200]
    rec['clientAfter'] = cv()
    return rec


def cmp(got, ref):
    if 'steps' not in got:
        return 'error'
    return 'match' if got['steps'] == ref else 'MISMATCH'


def a_seq(od, name, rounds):
    full = S.seq_a(rounds)
    setup, rnds = full[:2], full[2:]
    out = {'seq': name, 'rounds': rounds, 'calls': []}
    ok, fullref, _ = ref_run(full)
    out['fullRefOk'] = ok
    start = 0
    while start < len(rnds):
        # largest number of rounds, from `start`, that fits in one call
        n = len(rnds) - start
        while n >= 1:
            ok, _, st = ref_run(setup + rnds[:start])
            st = {k: v for k, v in st.items() if v}
            body = rnds[start:start + n]
            ok2, ref, _ = ref_run(body, st)
            got = chain(body, st, trace=True)
            time.sleep(1)
            okall = 'steps' in got and all(s['ok'] == 1 for s in got['steps'])
            res = cmp(got, ref)
            # rounds of the split must also equal the rounds of the one-piece reference of the whole sequence
            same_full = ok2 and ref == fullref[2 + start:2 + start + n]
            rec = {'firstRound': start, 'nRounds': n, 'result': res, 'allStepsOk': okall, 'refEqualsWholeSequenceRef': same_full,
                   'words': sum(len(s.get('w', [])) for s in got.get('steps', [])), **{k: v for k, v in got.items() if k != 'steps'}}
            if res != 'match':
                rec['got'] = got.get('steps'); rec['ref'] = ref
            print(name, {k: v for k, v in rec.items() if k not in ('got', 'ref')}, flush=True)
            if okall or n == 1:
                out['calls'].append(rec)
                start += n
                break
            n = max(1, n // 2)
    json.dump(out, open(os.path.join(od, f'l1126-{name}.json'), 'w'), indent=1)
    return out


def d_seq(od, n):
    steps = S.seq_d(n)
    base = 0x1000000
    pre = {}
    # find the mapping slot of the ERC-6909 balances from the slots the reference reads in a one-currency run
    reads = set()
    wd = world()

    class Spy(dict):
        def get(self, k, d=None):
            reads.add(k)
            return dict.get(self, k, d)
    wd.storage = Spy()
    wd.call(S.EOA, S.D, 0, S.enc_run(S.seq_d(1)), False, 0)
    p_found = None
    for p in range(0, 16):
        inner = keccak(S.D.to_bytes(32, 'big') + p.to_bytes(32, 'big'))
        k = int.from_bytes(keccak(base.to_bytes(32, 'big') + inner), 'big')
        if (PM, k) in reads:
            p_found = p; break
    assert p_found is not None, 'balance mapping slot not found'
    inner = keccak(S.D.to_bytes(32, 'big') + p_found.to_bytes(32, 'big'))
    for i in range(n):
        k = int.from_bytes(keccak((base + i).to_bytes(32, 'big') + inner), 'big')
        pre[(PM, k)] = 1
    # driver output array `out` is slot 0 of Seq: elements at keccak(0)+j
    o0 = int.from_bytes(keccak((0).to_bytes(32, 'big')), 'big')
    for j in range(64):
        pre[(S.D, o0 + j)] = 1
    ok, ref, _ = ref_run(steps, pre)
    got = chain(steps, pre, trace=True)
    rec = {'seq': f'd{n}', 'balanceMappingSlot': p_found, 'refOk': ok, 'result': cmp(got, ref),
           'words': sum(len(s.get('w', [])) for s in got.get('steps', [])), **{k: v for k, v in got.items() if k != 'steps'}}
    # the unmodified reference (empty state) must give the same words, so the pre-set slots change nothing observed
    ok0, ref0, _ = ref_run(steps)
    rec['refEqualsEmptyStateRef'] = ok0 and ref0 == ref
    if rec['result'] != 'match':
        rec['got'] = got.get('steps'); rec['ref'] = ref
    else:
        rec['lastWords'] = got['steps'][0]['w'][-2:]
    print({k: v for k, v in rec.items() if k not in ('got', 'ref')}, flush=True)
    json.dump(rec, open(os.path.join(od, f'l1126-d{n}.json'), 'w'), indent=1)
    return rec


if __name__ == '__main__':
    od = sys.argv[1]; names = sys.argv[2:] or ['a64', 'd300']
    for nm in names:
        if nm.startswith('a'):
            a_seq(od, nm, int(nm[1:]) // 16)
        elif nm.startswith('d'):
            d_seq(od, int(nm[1:]))
