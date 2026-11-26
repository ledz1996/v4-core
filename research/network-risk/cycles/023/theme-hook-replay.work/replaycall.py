"""Read-only simulation, on a network where a hook address is empty, of a replay of the original CREATE2-deployer call:
eth_call to 0x4e59b448 with the original salt and init code from an arbitrary sender (0x...5afe), then debug_traceCall with
the prestateTracer in diff mode to read the code and storage the replay would leave at the hook address. No transaction.
usage: replaycall.py <chainId> <url> <raw/init_*.hex> <hook>"""
import sys, json, hashlib
sys.path.insert(0, '.')
from rpcu import rpc
c, u, f, h = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].lower()
D2 = '0x4e59b44847b379578588920ca78fbf26c0b4956c'; S = '0x000000000000000000000000000000000000' + '5afe'
data = '0x' + open(f).read().strip()
out = {'chainId': c, 'url': u, 'hook': h, 'sender': S, 'client': [rpc(u, 'web3_clientVersion', [])]}
blk = rpc(u, 'eth_blockNumber', []); out['block'] = int(blk, 16)
out['codeBefore'] = rpc(u, 'eth_getCode', [h, blk]); out['deployerCodeLen'] = (len(rpc(u, 'eth_getCode', [D2, blk])) - 2) // 2
call = {'from': S, 'to': D2, 'data': data, 'gas': hex(15_000_000)}
try: out['ethCall'] = {'ok': True, 'ret': rpc(u, 'eth_call', [call, blk], tries=2)}
except Exception as e: out['ethCall'] = {'ok': False, 'err': str(e)[:500]}
try:
    tr = rpc(u, 'debug_traceCall', [call, blk, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}], tries=2)
    post = {k.lower(): v for k, v in tr.get('post', {}).items()}.get(h, {})
    code = post.get('code', '0x')
    out['trace'] = {'ok': True, 'postCodeLen': (len(code) - 2) // 2, 'postCodeSha256': hashlib.sha256(bytes.fromhex(code[2:])).hexdigest(), 'postStorage': post.get('storage', {}), 'postNonce': post.get('nonce')}
    open('raw/replay_runtime_%s_%s.hex' % (h[:10], c), 'w').write(code[2:])
except Exception as e: out['trace'] = {'ok': False, 'err': str(e)[:300]}
out['client'].append(rpc(u, 'web3_clientVersion', []))
json.dump(out, open('raw/replaycall_%s_%s.json' % (h[:10], c), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'codeBefore'}), 'codeBefore', out['codeBefore'][:10])
