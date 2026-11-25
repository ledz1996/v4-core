"""Do the pre-AP2 multicoin opcodes 0xcd (BALANCEMC) and 0xcf (CALLEX) execute today on the C-Chain?
A stub placed by state override runs ADDRESS, PUSH32 asset, <op>, and returns the top of stack; BALANCE as control.
Usage: python3 oldops.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc
URL = 'https://api.avax.network/ext/bc/C/rpc'; STUB = '0x00000000000000000000000000000000c0ffee0b'
res = {'clientVersion': rpc(URL, 'web3_clientVersion', [])}
asset = bytes([0x7f]) + b'\x00' * 31 + b'\x01'
tail = bytes([0x60, 0, 0x52, 0x60, 0x20, 0x60, 0, 0xf3])
progs = {'BALANCE control': bytes([0x30, 0x31]) + tail,
         '0xcd after ADDRESS,PUSH32': bytes([0x30]) + asset + bytes([0xcd]) + tail,
         '0xcf with 8 stack items': bytes([0x60, 0] * 8) + bytes([0xcf]) + tail}
for k, c in progs.items():
    try: r = rpc(URL, 'eth_call', [{'to': STUB, 'data': '0x', 'gas': '0x100000'}, 'latest', {STUB: {'code': '0x' + c.hex()}}])
    except Exception as e: r = 'ERR ' + str(e)
    res[k] = {'code': c.hex(), 'result': r}
res['clientVersionEnd'] = rpc(URL, 'web3_clientVersion', [])
json.dump(res, open(sys.argv[1], 'w'), indent=1); print(json.dumps(res, indent=1))
