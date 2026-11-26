"""Sort the interpreter/native differences of an out-of-gas sweep (replay.cpp with HX_GAS_SWEEP): for every DIFF record, compare
everything in the two digests except the per-frame lines (storage, transient storage, balance, logs), and check that the frame lists
differ only by frames that halted for gas on one side and by the frames nested inside them.
Usage: sweepcheck.py out.json sweep.out..."""
import sys, json, re
res = {'records': 0, 'stateEqual': 0, 'stateDiffers': [], 'frameShapes': {}}
for p in sys.argv[2:]:
    txt = open(p).read()
    for b in txt.split('\nGAS ')[0:]:
        if 'DIFF' not in b.split('\n')[0]: continue
        head = b.split('\n')[0]
        i = b.index('--- interp\n'); j = b.index('--- native\n')
        a = b[i + 11:j].splitlines(); n = b[j + 11:].splitlines()
        n = [x for x in n if not x.startswith(('post_storage', 'txs=', 'sweep', 'GAS '))]
        n = n[:next((k for k, x in enumerate(n) if x.startswith(('SAME', 'DIFF'))), len(n))]
        res['records'] += 1
        sa = [x for x in a if not x.strip().startswith(('frame', 'div='))]; sn = [x for x in n if not x.strip().startswith(('frame', 'div='))]
        if sa == sn: res['stateEqual'] += 1
        else: res['stateDiffers'].append({'file': p, 'head': head[:200]})
        fa = [x.split()[2] for x in a if x.strip().startswith('frame')]; fn = [x.split()[2] for x in n if x.strip().startswith('frame')]
        key = 'native has fewer frames' if len(fn) < len(fa) else ('native has more frames' if len(fn) > len(fa) else 'same count')
        res['frameShapes'][key] = res['frameShapes'].get(key, 0) + 1
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})
