# Print the chain of frames (type, to, selector, gas, gasUsed, error) from the root to every frame that calls a given address. Read-only RPC.
import json, sys, urllib.request
U, H, A = sys.argv[1], sys.argv[2], sys.argv[3].lower()
rq = urllib.request.Request(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceTransaction', 'params': [H, {'tracer': 'callTracer'}]}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
t = json.load(urllib.request.urlopen(rq, timeout=120))['result']
def walk(n, chain):
    me = (n.get('type'), n.get('to'), (n.get('input') or '')[:10], int(n.get('gas', '0x0'), 16), int(n.get('gasUsed', '0x0'), 16), n.get('error'), len(n.get('input') or '') // 2 - 1, (n.get('output') or '')[:74])
    if (n.get('to') or '').lower() == A:
        print(json.dumps(chain + [me]))
    for c in n.get('calls', []) or []: walk(c, chain + [me])
walk(t, [])
