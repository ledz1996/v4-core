"""Cycle 29 stablecoin-l1: tools/opdiff/battery.py and targeted.py vectors sent to Arc endpoints that state/networks.json
does not list (arc.drpc.org, arc-rpc.publicnode.com), each bracketed by arc_getVersion. Read-only.
Usage: python3 battery_urls.py <out.json> <url> [<url> ...]"""
import sys, os, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery as B  # noqa: E402
import targeted as T  # noqa: E402
from evm import rpc  # noqa: E402


def ver(url):
    try: return rpc(url, 'arc_getVersion', [], 20)
    except Exception as e: return str(e)[:100]  # noqa


out = {}
for url in sys.argv[2:]:
    r = {'before': ver(url)}
    for name, mod in (('battery', B), ('targeted', T)):
        code = mod.dispatcher() if hasattr(mod, 'dispatcher') else B.dispatcher()
        V = mod.vectors()
        done, bad, errors = mod.run(url, code, V) if hasattr(mod, 'run') else B.run(url, code, V)
        if errors and done < len(V):
            retry = [t for i, _ in errors for t in V[i:i + 600]]
            d2, b2, e2 = (mod.run if hasattr(mod, 'run') else B.run)(url, code, retry, size=150)
            done += d2; bad += b2; errors = e2
        r[name] = {'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:50], 'errors': errors[:10]}
        print(url, name, len(V), 'ran', done, 'mismatches', len(bad), 'errors', len(errors), flush=True)
    r['after'] = ver(url)
    out[url] = r
json.dump(out, open(sys.argv[1], 'w'), indent=1)
