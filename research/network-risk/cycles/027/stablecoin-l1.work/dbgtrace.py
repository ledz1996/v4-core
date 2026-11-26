import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l1126 as T
S = T.S
full = S.seq_a(4); setup, rnds = full[:2], full[2:]
start, n, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
ok, _, st = T.ref_run(setup + rnds[:start]); st = {k: v for k, v in st.items() if v}
body = rnds[start:start + n]
blk = T.rpc(T.URL, 'eth_blockNumber', [])
tx = {'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.D, 'data': '0x' + S.enc_run(body).hex(), 'gas': hex(T.GAS)}
t = T.rpc(T.URL, 'debug_traceCall', [tx, blk, {'tracer': 'callTracer', 'stateOverrides': T.overrides(st)}], timeout=300)
json.dump({'block': int(blk, 16), 'client': T.cv(), 'trace': t}, open(outp, 'w'))
def walk(c, d=0, path=''):
    err = c.get('error')
    if err or d < 2:
        print('  ' * d, c.get('type'), c.get('to'), int(c.get('gas', '0x0'), 16), int(c.get('gasUsed', '0x0'), 16), (c.get('input') or '')[:10], err, (c.get('output') or '')[:74], c.get('revertReason'))
    for x in c.get('calls', []) or []:
        walk(x, d + 1)
walk(t)
