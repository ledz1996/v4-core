"""Within each basic block, track which stack words are constants pushed in that block,
and classify the operands of shift, byte, division and modular instructions.
Usage: python3 -I operands.py <instrs.json> <out.json>"""
import sys, json
ins = json.load(open(sys.argv[1]))
ARITY = {'ADD':2,'MUL':2,'SUB':2,'DIV':2,'SDIV':2,'MOD':2,'SMOD':2,'ADDMOD':3,'MULMOD':3,'EXP':2,'SIGNEXTEND':2,'LT':2,'GT':2,'SLT':2,'SGT':2,'EQ':2,'ISZERO':1,'AND':2,'OR':2,'XOR':2,'NOT':1,'BYTE':2,'SHL':2,'SHR':2,'SAR':2,'KECCAK256':2,
 'ADDRESS':0,'CALLER':0,'CALLVALUE':0,'CALLDATALOAD':1,'CALLDATASIZE':0,'CALLDATACOPY':3,'CODECOPY':3,'RETURNDATASIZE':0,'RETURNDATACOPY':3,'SELFBALANCE':0,'POP':1,'MLOAD':1,'MSTORE':2,'MSTORE8':2,'SLOAD':1,'SSTORE':2,'TLOAD':1,'TSTORE':2,'MCOPY':3,
 'GAS':0,'MSIZE':0,'PC':0,'JUMPDEST':0,'CALL':7,'STATICCALL':6,'LOG0':2,'LOG1':3,'LOG2':4,'LOG3':5,'LOG4':6,'RETURN':2,'REVERT':2,'STOP':0,'INVALID':0,'JUMP':1,'JUMPI':2}
OUT = {'ADDRESS','CALLER','CALLVALUE','CALLDATALOAD','CALLDATASIZE','RETURNDATASIZE','SELFBALANCE','MLOAD','SLOAD','TLOAD','GAS','MSIZE','PC','CALL','STATICCALL','KECCAK256'}
res = []
st = []
for k, e in enumerate(ins):
    op = e['op']
    if op == 'JUMPDEST' or e['src'] == 'data': st = []
    def get(i):  # i = 0 top
        return st[-1 - i] if i < len(st) else ('?',)
    if op in ('SHL','SHR','SAR','BYTE','DIV','SDIV','MOD','SMOD','MULMOD','SIGNEXTEND'):
        n = ARITY[op]; args = [get(i) for i in range(n)]
        res.append({'pc': e['pc'], 'op': op, 'src': e['src'], 'fn': e['fn'], 'yul': e['yul'], 'operands': [('const 0x' + a[1]) if a[0] == 'c' else 'var' for a in args]})
    if op.startswith('PUSH'):
        st.append(('c', e['imm'] or '0'))
    elif op.startswith('DUP'):
        st.append(get(int(op[3:]) - 1))
    elif op.startswith('SWAP'):
        j = int(op[4:])
        while len(st) <= j: st.insert(0, ('?',))
        st[-1], st[-1 - j] = st[-1 - j], st[-1]
    elif op in ARITY:
        n = ARITY[op]
        for _ in range(n):
            if st: st.pop()
        if op in OUT or op not in ('POP','MSTORE','MSTORE8','SSTORE','TSTORE','MCOPY','CALLDATACOPY','CODECOPY','RETURNDATACOPY','LOG0','LOG1','LOG2','LOG3','LOG4','RETURN','REVERT','STOP','INVALID','JUMP','JUMPI','JUMPDEST'):
            st.append(('v',))
    else:
        st = []
    if op in ('JUMP','JUMPI','STOP','RETURN','REVERT','INVALID'): st = []
json.dump(res, open(sys.argv[2], 'w'), indent=0)
import collections
c = collections.Counter((r['op'], tuple(x if x == 'var' else 'const' for x in r['operands'])) for r in res)
for k, v in sorted(c.items()): print(k, v)
print('constant value shifted by a variable amount (SHL/SHR/SAR with operand0 var, operand1 const):')
for r in res:
    if r['op'] in ('SHL','SHR','SAR') and r['operands'][0] == 'var' and r['operands'][1] != 'var': print('  ', r['pc'], r['op'], r['operands'], r['src'], r['fn'])
print('MULMOD:')
for r in res:
    if r['op'] == 'MULMOD': print('  ', r['pc'], r['operands'], r['src'], r['yul'])
print('DIV/MOD with variable divisor:')
for r in res:
    if r['op'] in ('DIV','MOD','SDIV','SMOD') and r['operands'][1] == 'var': print('  ', r['pc'], r['op'], r['operands'], r['src'], r['yul'])
