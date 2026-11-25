"""Fetch the deployed PoolManager runtime code on Celo and X Layer and list which opcodes appear in
executable position (PUSH data skipped), to see whether any opcode that Karst or Lagoon activates or
reprices (CLZ 0x1e, DUPN/SWAPN/EXCHANGE 0xe6-0xe8) is reachable. Read-only. Usage: python3 opscan.py <out.json>"""
import json, sys, urllib.request, collections
NETS = {42220: ('https://forno.celo.org', '0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'),
        196: ('https://rpc.xlayer.tech', '0x360e68faccca8ca495c1b759fd9eee466db9fb32')}
def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=60))['result']
out = {}
for cid, (u, a) in NETS.items():
    code = bytes.fromhex(rpc(u, 'eth_getCode', [a, 'latest'])[2:])
    i = 0; ops = collections.Counter(); last = None
    while i < len(code):
        op = code[i]; ops[op] += 1; last = i
        i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
    out[cid] = {'len': len(code), 'endsInsidePush': i > len(code), 'clz': ops.get(0x1e, 0), 'dupnSwapnExchange': sum(ops.get(x, 0) for x in (0xe6, 0xe7, 0xe8)),
                'selfdestruct': ops.get(0xff, 0), 'distinctOps': len(ops), 'invalid_fe': ops.get(0xfe, 0)}
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(out)
