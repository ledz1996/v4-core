# List every failed frame in a mined transaction's call tree (callTracer), with depth, type, target, selector, error and gas. Read-only RPC.
import json, sys, urllib.request
U, H = sys.argv[1], sys.argv[2]
rq = urllib.request.Request(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceTransaction', 'params': [H, {'tracer': 'callTracer'}]}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
t = json.load(urllib.request.urlopen(rq, timeout=120))['result']
out = []
def walk(n, d, path):
    if 'error' in n: out.append({'depth': d, 'path': path, 'type': n.get('type'), 'to': n.get('to'), 'sel': (n.get('input') or '')[:10], 'error': n.get('error'), 'gas': int(n.get('gas', '0x0'), 16), 'gasUsed': int(n.get('gasUsed', '0x0'), 16), 'parentOk': True})
    for i, c in enumerate(n.get('calls', []) or []): walk(c, d + 1, path + [i])
walk(t, 0, [])
print(json.dumps({'tx': H, 'topError': t.get('error'), 'failed': out}, indent=1))
