"""L-848: battery and targeted vectors on OP Mainnet's mixed endpoint, each batch bracketed by
web3_clientVersion and kept only when both brackets name the same build. Goal: every batch
covered under each of the two builds. Seeds as in battery.py (20261124) and targeted.py (681)."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, call_code
import battery, targeted
URL = sys.argv[2] if len(sys.argv) > 2 else 'https://mainnet.optimism.io'
code = battery.dispatcher()
sets = {'battery': battery.vectors(), 'targeted': targeted.vectors()}
SIZE = 600
out = {'url': URL, 'batchSize': SIZE, 'seeds': {'battery': 20261124, 'targeted': 681}, 'sets': {}}
for name, V in sets.items():
    nb = (len(V) + SIZE - 1) // SIZE
    cover = {}   # build -> set of batch idx
    bad = {}; tries = 0; discarded = 0; errors = 0
    builds_seen = set()
    pending = {i for i in range(nb)}
    t0 = time.time()
    while time.time() - t0 < float(os.environ.get('BUDGET', '1500')):
        # choose a batch not yet covered by the build we expect to hit; we cannot choose the build, so cycle
        todo = [i for i in range(nb) if any(i not in cover.get(b, set()) for b in (builds_seen or {'?'}))] or []
        if len(builds_seen) >= 2 and all(len(cover.get(b, ())) == nb for b in builds_seen):
            break
        if not todo: todo = list(range(nb))
        i = todo[tries % len(todo)]; tries += 1
        batch = V[i * SIZE:(i + 1) * SIZE]; data = battery.encode(batch)
        try:
            v1 = rpc(URL, 'web3_clientVersion', [])
            res = call_code(URL, code, data, retries=1)
            v2 = rpc(URL, 'web3_clientVersion', [])
        except Exception as e:
            errors += 1; continue
        if v1 != v2:
            discarded += 1; continue
        builds_seen.add(v1)
        if i in cover.get(v1, set()):
            continue
        exp = battery.expected(batch, data)
        if len(res) != 32 * len(batch):
            errors += 1; continue
        for k, (t, e) in enumerate(zip(batch, exp)):
            got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
            if got != e:
                bad.setdefault(v1, []).append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
        cover.setdefault(v1, set()).add(i)
    r = {'vectors': len(V), 'batches': nb, 'requests': tries, 'discardedMixedBrackets': discarded, 'errors': errors,
         'perBuild': {b: {'batchesCovered': len(s), 'vectorsCovered': sum(len(V[i*SIZE:(i+1)*SIZE]) for i in s), 'mismatches': bad.get(b, [])} for b, s in cover.items()}}
    out['sets'][name] = r
    print(name, json.dumps({k: v for k, v in r.items() if k != 'perBuild'}), {b: (x['batchesCovered'], x['vectorsCovered'], len(x['mismatches'])) for b, x in r['perBuild'].items()}, flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
