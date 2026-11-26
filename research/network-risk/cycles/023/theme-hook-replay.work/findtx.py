"""Find the transaction that created a hook in a known block: direct CREATE (receipt contractAddress), a call to the CREATE2
deployer 0x4e59b448 (address recomputed), or else a callTracer trace of each transaction in the block until a CREATE or
CREATE2 frame with that address appears. usage: findtx.py url block hook [traceUrl]. Read only."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
from kk import c2
u, blk, h = sys.argv[1], int(sys.argv[2]), sys.argv[3].lower(); tu = sys.argv[4] if len(sys.argv) > 4 else u
D2 = '0x4e59b44847b379578588920ca78fbf26c0b4956c'; CX = '0xba5ed099633d3b313e4d5f7bdc1305d3c28ba5ed'
cv = [rpc(u, 'web3_clientVersion', []), rpc(tu, 'web3_clientVersion', [])]
b = rpc(u, 'eth_getBlockByNumber', [hex(blk), True])
assert len(rpc(u, 'eth_getCode', [h, hex(blk)])) > 2 and len(rpc(u, 'eth_getCode', [h, hex(blk - 1)])) <= 2
res = None
def walk(fr, path):
    if fr.get('type') in ('CREATE', 'CREATE2') and fr.get('to', '').lower() == h: return fr, path
    for i, ch in enumerate(fr.get('calls', []) or []):
        r = walk(ch, path + [i])
        if r: return r
for t in b['transactions']:
    to = (t['to'] or '').lower()
    if to == D2 and len(t['input']) > 66:
        inp = bytes.fromhex(t['input'][2:])
        if c2(D2, inp[:32], inp[32:]) == h: res = {'tx': t['hash'], 'how': 'direct call to CREATE2 deployer', 'from': t['from'], 'factory': D2, 'salt': '0x' + inp[:32].hex()}; break
    if not t['to']:
        rc = rpc(u, 'eth_getTransactionReceipt', [t['hash']])
        if (rc.get('contractAddress') or '').lower() == h: res = {'tx': t['hash'], 'how': 'CREATE transaction', 'from': t['from'], 'nonce': int(t['nonce'], 16)}; break
if not res:
    for t in b['transactions']:
        try: tr = rpc(tu, 'debug_traceTransaction', [t['hash'], {'tracer': 'callTracer'}], tries=2)
        except Exception as e: print('trace error', t['hash'], str(e)[:200]); continue
        r = walk(tr, [])
        if r:
            fr, path = r
            parent = tr
            for i in path[:-1]: parent = parent['calls'][i]
            res = {'tx': t['hash'], 'how': fr['type'] + ' inside a call', 'from': t['from'], 'txTo': t['to'], 'txSel': t['input'][:10], 'factory': fr['from'], 'path': path,
                   'createInputLen': (len(fr.get('input', '0x')) - 2) // 2, 'createInputHead': fr.get('input', '')[:200]}
            open('raw/createinput_%s.hex' % h[:10], 'w').write(fr.get('input', '0x')[2:]); break
cv.append(rpc(u, 'web3_clientVersion', []))
out = {'url': u, 'traceUrl': tu, 'client': cv, 'block': blk, 'hook': h, 'txCount': len(b['transactions']), 'result': res}
json.dump(out, open('raw/findtx_%s_%d.json' % (h[:10], blk), 'w'), indent=1); print(json.dumps(out))
