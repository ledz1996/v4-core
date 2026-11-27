"""Cycle 31, Task 4: for the 128 un-entered value blocks, which emit paths of the gcc build have run in the x86 model
and on what states. Literal-ness of operands is taken from the logged real state of each instruction.
usage: task4.py -> out/task4.json"""
import json, collections, os, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(W, 'scripts'))
from blockops import opname
ops = json.load(open(os.path.join(W, 'out/value128-ops.json')))['blocks']
shift = json.load(open(os.path.join(W, 'out/model/realshift.json')))
runreal = {int(r['pc'], 16) for r in shift['sites'] if not r.get('stop') and not r['flagged']}
want = {int(k, 16) for k in ops}
NARGS = {'ADD': 2, 'SUB': 2, 'MUL': 2, 'DIV': 2, 'MOD': 2, 'MULMOD': 3, 'AND': 2, 'OR': 2, 'XOR': 2, 'LT': 2, 'GT': 2, 'SLT': 2,
         'SGT': 2, 'EQ': 2, 'SHL': 2, 'SHR': 2, 'SIGNEXTEND': 2, 'ISZERO': 1}
status = collections.defaultdict(lambda: {'sites': 0, 'blocks': set()})
for l in open(os.path.join(W, 'out/states.jsonl')):
    d = json.loads(l)
    if d['b'] not in want: continue
    if d['w'] == 'e': key = 'block entry (block_prologue): run on generated states in cycle 30'
    elif d['w'] == 't': key = 'terminator %d (jump, jumpi, fallthrough, return, revert; write_to_final_stack_offsets): stack writer run on generated states in cycle 30, rest not run' % (d['op'] - 1000)
    else:
        op = opname(d['pc']); n = NARGS.get(op, 0)
        lit = [('lit' in e) for e in d['elems'][-n:]] if n else []
        if d['pc'] in runreal: key = '%s with literal count: whole Emitter::%s run on the real state in cycle 31' % (op, op.lower())
        elif op in ('MUL', 'MULMOD', 'DIV', 'MOD', 'SIGNEXTEND') and any(lit):
            key = '%s with a literal operand: literal arm run on generated operands in cycles 28 and 29, not on this state' % op
        elif op.startswith('PUSH') or op.startswith('DUP') or op.startswith('SWAP') or op == 'POP':
            key = '%s: virtual stack only (push, dup, swap, pop bookkeeping); Stack::push and pop run in cycle 30, the rest not run' % (op.rstrip('0123456789'))
        else:
            key = '%s%s: not run in the gcc model' % (op, ' (all non-literal)' if n and not any(lit) else (' (some literal)' if n else ''))
    status[key]['sites'] += 1; status[key]['blocks'].add(hex(d['b']))
out = {k: {'sites': v['sites'], 'blocks': sorted(v['blocks'], key=lambda x: int(x, 16))} for k, v in sorted(status.items())}
json.dump(out, open(os.path.join(W, 'out/task4.json'), 'w'), indent=1)
for k, v in out.items(): print(v['sites'], len(v['blocks']), k)
