"""Cycle 29 stablecoin-l1: positive control for scen_seq.py. One D scenario is sent to Tempo with every MULMOD (0x09)
opcode of the PoolManager runtime that is not push data turned into ADDMOD (0x08), and the reply is compared with the
unmodified reference. A comparison that can see faults must report a difference. Read-only."""
import sys, json
sys.argv = ['x']
import scen_seq as Q
X = Q.X
nm = [k for k in X.SCEN if k.startswith('D donations 3')][0]
sc = X.SCEN[nm]
cs = X.codes_for(X.PM, [sc['key']]); cs[Q.SEQ] = Q.STUB
wd = X.P.World(cs); data = Q.enc(sc); ok, ret = wd.call(X.EOA, Q.SEQ, 0, data, False, 0)
code = bytearray(cs[X.PM]); i = 0; n = 0
while i < len(code):
    op = code[i]
    if op == 0x09: code[i] = 0x08; n += 1
    i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
so = {'0x%040x' % a: {'code': '0x' + b.hex()} for a, b in cs.items()}
so['0x%040x' % X.PM] = {'code': '0x' + code.hex()}
g = bytes.fromhex(Q.rpc('https://rpc.mainnet.tempo.xyz', 'eth_call', [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % Q.SEQ,
    'data': '0x' + data.hex(), 'gas': hex(150_000_000)}, 'latest', so], timeout=180)[2:])
r = {'scenario': nm, 'mulmodSitesChanged': n, 'sameAsReference': g == ret, 'refSteps': [s[0] for s in Q.split(ret)],
     'gotSteps': [s[0] for s in Q.split(g)]}
print(r); json.dump(r, open('out/control.json', 'w'), indent=1)
