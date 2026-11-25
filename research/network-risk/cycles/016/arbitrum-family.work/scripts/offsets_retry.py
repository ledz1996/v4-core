# Rerun the vectors of offsets.json whose answer was an HTTP error, and update the file.
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offsets.py')).read().split('out = {}; bad = 0')[0]
g = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offsets.py')}; exec(src, g)
d = json.load(open(sys.argv[1]))
for cid, res in d.items():
    for r in res:
        if r['got'].startswith('ERR:HTTP'):
            o = int(r['offset'], 16); code = g['assemble'](g['prog'](r['kind'], o))
            time.sleep(3)
            try: got = g['call_code'](g['NETS'][int(cid)], code, g['CD'], gas=1_000_000).hex()
            except Exception as e:
                got = 'FAIL' if 'out of bounds' in str(e) or 'revert' in str(e).lower() or 'invalid' in str(e).lower() else 'ERR:' + str(e)[:120]
            r['got'] = got[:140]; r['ok'] = got[:140] == r['expected']; r['retried'] = True
            print(cid, r['kind'], r['offset'], r['ok'], got[:60])
json.dump(d, open(sys.argv[1], 'w'), indent=0)
for cid, res in d.items(): print(cid, 'vectors', len(res), 'mismatches', sum(not r['ok'] for r in res))
