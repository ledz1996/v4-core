"""Tempo: what SELFBALANCE, a value CALL of 1 and BALANCE return inside eth_call with and without a balance override.
Usage: python3 tempo_value_probe.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common26  # noqa  (sets the path to tools/opdiff)
from evm import rpc
code = bytes.fromhex('47' '5f52' '5f5f5f5f' '6001' '610b0b' '5a' 'f1' '602052' '610b0b' '31' '604052' '6060' '5f' 'f3')  # SELFBALANCE; CALL(gas, 0xb0b, 1); BALANCE(0xb0b)
A = '0x00000000000000000000000000000000beef0002'; url = 'https://rpc.mainnet.tempo.xyz'
out = {'client': rpc(url, 'web3_clientVersion', []), 'block': rpc(url, 'eth_blockNumber', [])}
for name, ov in (('no balance override', {A: {'code': '0x' + code.hex()}}), ('balance override 10', {A: {'code': '0x' + code.hex(), 'balance': '0xa'}})):
    r = rpc(url, 'eth_call', [{'to': A, 'data': '0x'}, out['block'], ov])
    out[name] = {'selfbalance, call ok, balance(0xb0b)': [int(r[2 + 64 * i:2 + 64 * (i + 1)], 16) for i in range(3)]}
out['eth_getBalance(0xb0b)'] = rpc(url, 'eth_getBalance', ['0x0000000000000000000000000000000000000b0b', out['block']])
out['clientAfter'] = rpc(url, 'web3_clientVersion', [])
print(out); json.dump(out, open(sys.argv[1], 'w'), indent=1)
