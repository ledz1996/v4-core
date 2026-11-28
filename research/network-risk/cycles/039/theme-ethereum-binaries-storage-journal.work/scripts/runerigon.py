"""usage: python3 -I runerigon.py <out.json> <fault|none> <ntrees> <npm>
Cycle 36 sequences (a)-(h), t, random frame trees (seed 36_2026_11_27) and PoolManager reentry shapes
(pmshapes.py, seed 36_2026_11_27+1) with cachemodel.Core replaced by erigonc.BinCore (erigon v3.8.2 binary)."""
import json, os, random, sys, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import erigonc as E
sys.path.insert(0, E.C36)
import seqs as S36, cachemodel as CM
OUT, FAULT, NT, NPM = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fault = None if FAULT == 'none' else FAULT
S36.Core = E.BinCore
res = {'binary': E.BIN, 'fault': FAULT, 'sequences': {}, 'random': {}, 'pm': None, 'errors': [], 'started': time.time()}
for name, fn in S36.SEQS.items():
    m = S36.M(fault); fn(m)
    res['sequences'][name] = {'reads': m.c.reads, 'hits': m.c.hits, 'fills': m.c.fills, 'stale': m.c.stale, 'gasStale': m.c.gas_stale}
    # the same sequence on the cycle 36 Python model, for comparison of hit counts
    mm = S36.M.__new__(S36.M); mm.raw = {}; mm.tr = {}; mm.c = CM.Core(mm.raw, None); mm.static = False; fn(mm)
    res['sequences'][name]['modelHits'] = mm.c.hits; res['sequences'][name]['modelStale'] = len(mm.c.stale)
rnd = random.Random(36_2026_11_27); tot = {'trees': NT, 'reads': 0, 'hits': 0, 'stale': 0, 'gasStale': 0, 'treesWithStale': 0, 'first': None, 'hitsDifferFromModel': 0}
for i in range(NT):
    st = rnd.getstate()
    m = S36.M(fault)
    try:
        S36.rand_tree(m, rnd, [60])
    except E.Stop as e:
        res['errors'].append({'tree': i, 'error': str(e)}); continue
    r2 = random.Random(); r2.setstate(st)
    mm = S36.M.__new__(S36.M); mm.raw = {}; mm.tr = {}; mm.c = CM.Core(mm.raw, None); mm.static = False; S36.rand_tree(mm, r2, [60])
    tot['reads'] += m.c.reads; tot['hits'] += m.c.hits; tot['stale'] += len(m.c.stale); tot['gasStale'] += len(m.c.gas_stale)
    tot['hitsDifferFromModel'] += m.c.hits != mm.c.hits
    if m.c.stale or m.c.gas_stale:
        tot['treesWithStale'] += 1
        if tot['first'] is None: tot['first'] = {'tree': i, 'stale': m.c.stale, 'gasStale': m.c.gas_stale}
res['random'] = tot
if NPM:
    import pmshapes as PMS
    PMS.Core = E.BinCore
    pm = PMS.P.fetch_code(); rnd = random.Random(36_2026_11_27 + 1)
    pt = {'scenarios': 0, 'pmCodeSha256': hashlib.sha256(pm).hexdigest(), 'sloads': 0, 'hits': 0, 'stale': 0, 'mismatch': 0, 'reentrantPmWrites': 0, 'first': None}
    for i in range(NPM):
        desc, data, hook = PMS.scenario(rnd, i)
        rw, ok1, ret1 = PMS.run(PMS.RefWorld, pm, hook, data)
        try:
            cw, ok2, ret2 = PMS.run(PMS.CachedWorld, pm, hook, data, fault=fault)
        except E.Stop as e:
            res['errors'].append({'pm': i, 'error': str(e)}); continue
        same = ret1 == ret2 and ok1 == ok2 and rw.sl == cw.sl and rw.ss == cw.ss and dict(rw.storage) == dict(cw.storage)
        pt['scenarios'] += 1; pt['sloads'] += len(cw.sl); pt['hits'] += cw.core.hits; pt['stale'] += len(cw.core.stale)
        pt['reentrantPmWrites'] += cw.reentrant_writes
        if not same or cw.core.stale:
            pt['mismatch'] += 1
            if pt['first'] is None: pt['first'] = {'scenario': i, 'desc': desc, 'stale': cw.core.stale[:5], 'data': data.hex(), 'hook': hook.hex(), 'ret1': ret1.hex(), 'ret2': ret2.hex()}
    res['pm'] = pt
mach = E.BinCore.shared_machine
res['functionsRun'] = sorted(set(mach.prog.names.values())); res['instructionsVisited'] = len(mach.visited)
res['stubbed'] = sorted(mach.stubbed); res['faultHits'] = mach.fault_hits; res['elapsed'] = time.time() - res['started']
json.dump(res, open(OUT, 'w'), indent=1)
print(FAULT, 'seq stale:', sorted(k for k, v in res['sequences'].items() if v['stale'] or v['gasStale']),
      'hits', {k: (v['hits'], v['modelHits']) for k, v in res['sequences'].items()}, 'random', {k: tot[k] for k in ('reads', 'hits', 'stale', 'treesWithStale', 'hitsDifferFromModel')},
      'pm', res['pm'] and {k: res['pm'][k] for k in ('scenarios', 'sloads', 'hits', 'stale', 'mismatch')}, 'errors', len(res['errors']), 'faultHits', mach.fault_hits, '%.0fs' % res['elapsed'])
