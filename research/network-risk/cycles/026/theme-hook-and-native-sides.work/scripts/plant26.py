"""Show that task4.py can fail: plant one-unit faults into a copy of the reference results and count what is caught.
Usage: python3 plant26.py <cases.json> <ref.json> <outdir>. Plants (deterministic, seed none): (a) PoolManager balance of
currency 1 one unit lower at the end, (b) hook delta of currency 0 one unit higher, (c) count after the last action plus one."""
import sys, os, json, subprocess, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import decode_words
cases = {str(c['id']): c for c in json.load(open(sys.argv[1]))['cases']}
ref = json.load(open(sys.argv[2])); od = sys.argv[3]
out = {}
for plant in ('pm-balance', 'hook-delta', 'count'):
    r = copy.deepcopy(ref); n = 0
    for k, v in r['results'].items():
        c = cases[k]
        if not v.get('w') or not v['ok'] or c['group'] not in ('D', 'F', 'G'): continue
        w = [int(x, 16) for x in v['w']]; nact = c['nact']
        i_deltas = 8 + 6 * nact; nh = w[i_deltas + 6]; i_after = i_deltas + 7 + min(nh, 24) + 6 + 2
        if plant == 'pm-balance': w[i_after + 1] -= 1
        elif plant == 'hook-delta': w[i_deltas + 2] = (w[i_deltas + 2] + 1) % (1 << 256)
        else: w[8 + 6 * (nact - 1) + 4] += 1
        v['w'] = [hex(x) for x in w]; n += 1
    p = os.path.join(od, f'plant-{plant}.json'); json.dump(r, open(p, 'w'))
    t = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'task4.py'), sys.argv[1], p, p + '.task4.json'], capture_output=True, text=True)
    out[plant] = {'planted': n, 'task4': t.stdout.strip()}
    print(plant, n, t.stdout.strip())
json.dump(out, open(os.path.join(od, 'plant-summary.json'), 'w'), indent=1)
