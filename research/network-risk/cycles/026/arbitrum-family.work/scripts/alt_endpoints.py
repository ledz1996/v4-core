"""Cycle 26: battery.py and targeted.py vectors (unchanged generators and seeds) on
public Robinhood Chain endpoints that answer as other Nitro builds than the official
endpoint. Each batch is bracketed by web3_clientVersion; the answers are compared with
the specified word. Usage: python3 alt_endpoints.py <out.json> <url> [<url> ...]
"""
import sys, os, json, time
OPD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, OPD)
from evm import rpc, call_code
import battery, targeted


def cv(u):
    try: return rpc(u, 'web3_clientVersion', [], timeout=30)
    except Exception as e: return 'ERR ' + str(e)[:80]  # noqa


res = []
code = battery.dispatcher()
for u in sys.argv[2:]:
    for name, V in (('battery', battery.vectors()), ('targeted', targeted.vectors())):
        versions = set(); bad = []; done = 0; errs = []
        for i in range(0, len(V), 600):
            batch = V[i:i + 600]; data = battery.encode(batch); exp = battery.expected(batch, data)
            a = cv(u)
            try:
                r = None
                for k in range(3):
                    try: r = call_code(u, code, data); break
                    except Exception as e:  # noqa
                        err = str(e)[:120]; time.sleep(3 * (k + 1))
                if r is None: errs.append((i, err)); continue
            finally:
                b = cv(u); versions.update([a, b])
            if len(r) != 32 * len(batch): errs.append((i, 'short %d' % len(r))); continue
            for k, (t, e) in enumerate(zip(batch, exp)):
                g = int.from_bytes(r[32 * k:32 * k + 32], 'big')
                if g != e: bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(g), 'want': hex(e), 'brackets': [a, b]})
            done += len(batch)
        row = {'url': u, 'set': name, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:200], 'errors': errs[:20], 'clientVersions': sorted(versions)}
        print(json.dumps({k: row[k] for k in ('url', 'set', 'vectors', 'ran', 'mismatchCount', 'clientVersions')}), len(errs), flush=True)
        res.append(row)
        json.dump(res, open(sys.argv[1], 'w'), indent=1)
