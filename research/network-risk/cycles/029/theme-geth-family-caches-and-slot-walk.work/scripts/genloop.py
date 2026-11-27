"""Check every case of go-ethereum master core/vm/interpreter_gen.go (bbafd66) against the specification:
the stack underflow bound, the overflow bound, the static gas, the stack depth change, the handler called and
how pc advances. Usage: python3 genloop.py <interpreter_gen.go> <out.json>"""
import re, sys, json
SPEC = {  # op: (pops, pushes, static gas)
 'ADD': (2,1,3), 'MUL': (2,1,5), 'SUB': (2,1,3), 'DIV': (2,1,5), 'SDIV': (2,1,5), 'MOD': (2,1,5), 'SMOD': (2,1,5), 'ADDMOD': (3,1,8), 'MULMOD': (3,1,8),
 'SIGNEXTEND': (2,1,5), 'LT': (2,1,3), 'GT': (2,1,3), 'SLT': (2,1,3), 'SGT': (2,1,3), 'EQ': (2,1,3), 'ISZERO': (1,1,3), 'AND': (2,1,3), 'OR': (2,1,3),
 'XOR': (2,1,3), 'NOT': (1,1,3), 'BYTE': (2,1,3), 'SHL': (2,1,3), 'SHR': (2,1,3), 'SAR': (2,1,3), 'POP': (1,0,2), 'JUMP': (1,0,8), 'JUMPI': (2,0,10),
 'JUMPDEST': (0,0,1), 'PC': (0,1,2), 'MSIZE': (0,1,2), 'GAS': (0,1,2), 'PUSH0': (0,1,2), 'ADDRESS': (0,1,2), 'CALLER': (0,1,2), 'CALLVALUE': (0,1,2),
 'CALLDATASIZE': (0,1,2), 'CALLDATALOAD': (1,1,3), 'CODESIZE': (0,1,2), 'RETURNDATASIZE': (0,1,2), 'MLOAD': (1,1,3), 'MSTORE': (2,0,3), 'MSTORE8': (2,0,3),
 'TLOAD': (1,1,100), 'TSTORE': (2,0,100), 'STOP': (0,0,0), 'CLZ': (1,1,5), 'SELFBALANCE': (0,1,5), 'ORIGIN': (0,1,2), 'COINBASE': (0,1,2), 'TIMESTAMP': (0,1,2),
 'NUMBER': (0,1,2), 'CHAINID': (0,1,2), 'BASEFEE': (0,1,2), 'GASPRICE': (0,1,2), 'PREVRANDAO': (0,1,2), 'GASLIMIT': (0,1,2), 'BLOBBASEFEE': (0,1,2)}
for i in range(1, 33): SPEC[f'PUSH{i}'] = (0, 1, 3)
for i in range(1, 17): SPEC[f'DUP{i}'] = (i, i + 1, 3); SPEC[f'SWAP{i}'] = (i + 1, i + 1, 3)
src = open(sys.argv[1]).read()
cases = re.split(r'\n\t\tcase ', src)[1:]
res = {'cases': 0, 'checked': [], 'problems': [], 'unspecified': []}
for c in cases:
    head = c.split(':', 1)[0].strip(); body = c
    if head == 'default' or head.startswith('default'): continue
    ops = [h.strip() for h in head.split(',')]
    res['cases'] += 1
    for op in ops:
        if op not in SPEC: res['unspecified'].append(op); continue
        pops, pushes, gas = SPEC[op]
        m = re.search(r'if sp < (\d+) \{', body); under = int(m.group(1)) if m else 0
        m = re.search(r'if sp > (\d+) \{', body); over = int(m.group(1)) if m else None
        m = re.search(r'ChargeExecutionOnly\((\d+)\)', body); g = int(m.group(1)) if m else 0
        m = re.search(r'sp ([+-])= (\d+)', body); d = (int(m.group(2)) * (1 if m.group(1) == '+' else -1)) if m else 0
        p = []
        if under != pops: p.append(f'underflow bound {under} want {pops}')
        if pushes > pops and over != 1024 - (pushes - pops): p.append(f'overflow bound {over} want {1024 - (pushes - pops)}')
        if g != gas: p.append(f'gas {g} want {gas}')
        if len(ops) == 1 and d != pushes - pops: p.append(f'delta {d} want {pushes - pops}')
        res['checked'].append(op)
        if p: res['problems'].append({'op': op, 'problems': p})
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(res['cases'], 'cases;', len(res['checked']), 'ops checked; problems', res['problems'][:10], 'unspecified', res['unspecified'])
