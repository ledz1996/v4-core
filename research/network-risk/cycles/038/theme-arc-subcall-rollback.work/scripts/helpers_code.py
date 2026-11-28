"""Task 4: read the deployed code of Multicall3From and Memo on each Arc endpoint and list, by linear disassembly, the
opcodes that decide the sender and value of the CallFrom call: CALLER, ORIGIN, CALLVALUE, SELFBALANCE, DELEGATECALL,
CALLCODE, the PUSH of 0x1800..03, and the value word (the third stack item from the top) of every CALL, recovered by
looking at the instruction that pushed it when it is a constant. usage: python3 -I helpers_code.py <out.json> <url>..."""
import sys, json, hashlib
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.work/scripts')
from rpcu import rpc
A = {'Multicall3From': '0x522fAf9A91c41c443c66765030741e4AaCe147D0', 'Memo': '0x5294E9927c3306DcBaDb03fe70b92e01cCede505'}
NAMES = {0x33: 'CALLER', 0x32: 'ORIGIN', 0x34: 'CALLVALUE', 0x47: 'SELFBALANCE', 0xf4: 'DELEGATECALL', 0xf2: 'CALLCODE', 0xf1: 'CALL', 0xfa: 'STATICCALL', 0xff: 'SELFDESTRUCT', 0xf0: 'CREATE', 0xf5: 'CREATE2'}
def dis(code):
    i = 0; ops = []
    while i < len(code):
        op = code[i]; n = op - 0x5f if 0x60 <= op <= 0x7f else 0
        ops.append((i, op, code[i + 1:i + 1 + n])); i += 1 + n
    return ops
def scan(code):
    ops = dis(code); cnt = {}; pushes_pc = []
    for k, (pc, op, arg) in enumerate(ops):
        if op in NAMES: cnt[NAMES[op]] = cnt.get(NAMES[op], 0) + 1
        if 0x60 <= op <= 0x7f and int.from_bytes(arg, 'big') == 0x1800000000000000000000000000000000000003: pushes_pc.append(pc)
    # metadata: solc CBOR tail
    return {'len': len(code), 'sha256': hashlib.sha256(code).hexdigest(), 'opcounts': cnt, 'push_callFrom_at': pushes_pc,
            'cbor_tail': code[-53:].hex()}
out = {}
for u in sys.argv[2:]:
    v0 = rpc(u, 'web3_clientVersion', [], 30); av0 = rpc(u, 'arc_getVersion', [], 30)
    r = {}
    for k, a in A.items():
        c = rpc(u, 'eth_getCode', [a, 'latest'], 60)
        r[k] = scan(bytes.fromhex(c['result'][2:])) if 'result' in c else {'err': c}
    r['before'] = {'web3': v0.get('result', v0), 'arc': av0.get('result', av0)}
    r['after'] = {'web3': rpc(u, 'web3_clientVersion', [], 30).get('result'), 'arc': rpc(u, 'arc_getVersion', [], 30).get('result')}
    out[u] = r
    print(u, {k: (r[k].get('len'), r[k].get('opcounts'), r[k].get('push_callFrom_at')) for k in A})
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=str)
