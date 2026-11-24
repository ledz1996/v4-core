"""Map every instruction of the built runtime to a source location and to the enclosing
source function, using the deployed source map of solc 0.8.26.
Usage: python3 -I map.py <full.json> <repo root> <out instrs.json> <out ranges.json>"""
import sys, json, bisect
full, root, out_i, out_r = sys.argv[1:5]
b = json.load(open(full)); asts = json.load(open(full + '.ast.json'))
code = bytes.fromhex(b['runtime'])
NAMES = {}
for i, n in enumerate('STOP ADD MUL SUB DIV SDIV MOD SMOD ADDMOD MULMOD EXP SIGNEXTEND'.split()): NAMES[i] = n
for i, n in enumerate('LT GT SLT SGT EQ ISZERO AND OR XOR NOT BYTE SHL SHR SAR'.split()): NAMES[0x10 + i] = n
NAMES[0x20] = 'KECCAK256'
for i, n in enumerate('ADDRESS BALANCE ORIGIN CALLER CALLVALUE CALLDATALOAD CALLDATASIZE CALLDATACOPY CODESIZE CODECOPY GASPRICE EXTCODESIZE EXTCODECOPY RETURNDATASIZE RETURNDATACOPY EXTCODEHASH'.split()): NAMES[0x30 + i] = n
for i, n in enumerate('BLOCKHASH COINBASE TIMESTAMP NUMBER PREVRANDAO GASLIMIT CHAINID SELFBALANCE BASEFEE BLOBHASH BLOBBASEFEE'.split()): NAMES[0x40 + i] = n
for i, n in enumerate('POP MLOAD MSTORE MSTORE8 SLOAD SSTORE JUMP JUMPI PC MSIZE GAS JUMPDEST TLOAD TSTORE MCOPY PUSH0'.split()): NAMES[0x50 + i] = n
for i in range(32): NAMES[0x60 + i] = 'PUSH%d' % (i + 1)
for i in range(16): NAMES[0x80 + i] = 'DUP%d' % (i + 1); NAMES[0x90 + i] = 'SWAP%d' % (i + 1)
for i in range(5): NAMES[0xa0 + i] = 'LOG%d' % i
for o, n in {0xf0: 'CREATE', 0xf1: 'CALL', 0xf2: 'CALLCODE', 0xf3: 'RETURN', 0xf4: 'DELEGATECALL', 0xf5: 'CREATE2', 0xfa: 'STATICCALL', 0xfd: 'REVERT', 0xfe: 'INVALID', 0xff: 'SELFDESTRUCT'}.items(): NAMES[o] = n

# disassemble
ins = []; i = 0
while i < len(code):
    op = code[i]; k = op - 0x5f if 0x60 <= op <= 0x7f else 0
    ins.append({'pc': i, 'op': NAMES.get(op, hex(op)), 'imm': code[i + 1:i + 1 + k].hex() if k else None})
    i += 1 + k
# source map
ent = b['sourceMap'].split(';'); prev = ['0', '0', '-1', '-', '0']
print("sourcemap entries", len(ent), "instructions", len(ins))
NMAP = len(ent)
ent += [""] * (len(ins) - len(ent))
srcs = {}
for sid, path in b['srcIds'].items():
    p = path
    if p.startswith('solmate/'): p = 'lib/solmate/' + p[len('solmate/'):]
    try: srcs[int(sid)] = (path, open(root + '/' + p, 'rb').read())
    except FileNotFoundError: srcs[int(sid)] = (path, b'')
lines = {sid: [0] + [j + 1 for j, c in enumerate(t) if c == 10] for sid, (_, t) in srcs.items()}
def line(sid, off): return bisect.bisect_right(lines[sid], off)
# function spans from AST
funcs = {}
def walk(n, sid, contract):
    if isinstance(n, dict):
        nt = n.get('nodeType')
        if nt == 'ContractDefinition': contract = n['name']
        if nt in ('FunctionDefinition', 'ModifierDefinition'):
            s, l, _ = map(int, n['src'].split(':'))
            nm = n.get('name') or n.get('kind')
            funcs.setdefault(sid, []).append((s, s + l, '%s.%s' % (contract, nm)))
        for v in n.values(): walk(v, sid, contract)
    elif isinstance(n, list):
        for v in n: walk(v, sid, contract)
for path, a in asts.items():
    sid = [int(k) for k, v in b['srcIds'].items() if v == path][0]
    walk(a, sid, None)
def enclosing(sid, s, e):
    best = None
    for fs, fe, nm in funcs.get(sid, []):
        if fs <= s and e <= fe and (best is None or fe - fs < best[1] - best[0]): best = (fs, fe, nm)
    return best[2] if best else None
for k, e in enumerate(ins):
    if k >= NMAP:
        e.update({'jt': '-', 'src': 'data', 'fn': '<data: end marker and CBOR metadata, no source map entry>', 'text': ''}); continue
    f = ent[k].split(':')
    for j in range(len(f)):
        if f[j] != '': prev[j] = f[j]
    s, l, sid, jt = int(prev[0]), int(prev[1]), int(prev[2]), prev[3]
    e['jt'] = jt
    if sid in srcs:
        path, _ = srcs[sid]
        e['src'] = '%s:%d' % (path, line(sid, s)) + ('-%d' % line(sid, s + l) if line(sid, s + l) != line(sid, s) else '')
        e['fn'] = enclosing(sid, s, s + l) or ('<%s contract-level>' % path)
        e['text'] = srcs[sid][1][s:s + l].decode('utf8', 'replace')[:160]
    else:
        e['src'] = 'generated:%d' % sid if sid >= 0 else '-'; e['fn'] = '<compiler-generated>' if sid >= 0 else '<no source>'
        e['text'] = ''
# yul function entry points
entries = sorted((v['entryPoint'], k) for k, v in b['functionDebugData'].items() if v.get('entryPoint') is not None)
ep = [x[0] for x in entries]
for k, e in enumerate(ins):
    if k >= NMAP: e['yul'] = '<data>'; continue
    j = bisect.bisect_right(ep, e['pc']) - 1
    e['yul'] = entries[j][1] if j >= 0 else '<entry/dispatcher>'
json.dump(ins, open(out_i, 'w'))
# ranges: consecutive instructions with the same (yul function, source function)
ranges = []
for e in ins:
    key = (e['yul'], e['fn'])
    if ranges and ranges[-1]['key'] == key: ranges[-1]['end'] = e['pc']; ranges[-1]['n'] += 1
    else: ranges.append({'key': key, 'start': e['pc'], 'end': e['pc'], 'n': 1})
json.dump([{'start': r['start'], 'end': r['end'], 'instructions': r['n'], 'yulFunction': r['key'][0], 'sourceFunction': r['key'][1]} for r in ranges], open(out_r, 'w'), indent=0)
print(len(ins), 'instructions', len(ranges), 'ranges', len(entries), 'yul entry points')
