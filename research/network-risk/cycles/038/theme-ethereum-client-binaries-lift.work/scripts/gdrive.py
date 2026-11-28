"""Cycle 38: runs the vector sets of drive.py through the whole generated loop of geth v1.17.10 (gloop.py).
Each program pushes the operands of K cases with PUSH1..PUSH4, PUSH8, PUSH20 or PUSH32 (the widths the switch
handles inline, chosen as the smallest that holds the word, or PUSH32 on every third case), runs the opcode, leaves
the result on the stack, and ends with STOP. The words left on the stack are compared with Python integers. If a
program fails as a whole, its cases are rerun one by one so every failing case is recorded in full.
usage: python3 -I gdrive.py <set> <shard> <nshard> <out.json> [fault]
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goshim as G, gloop, targets
import gfaults

SET, SHARD, NSHARD, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
K = int(os.environ.get('K', '250'))

# the vector generators of drive.py, without running drive.py's own model
src = open(os.path.join(HERE, 'drive.py')).read()
src = src[:src.index('fspec = F.get')]
saved = sys.argv; sys.argv = ['drive.py', 'geth-amd64', SET, '0', '1', '/dev/null']
g = {'__name__': 'gen', '__file__': os.path.join(HERE, 'drive.py')}
exec(compile(src, 'drive.py', 'exec'), g)
sys.argv = saved
GEN, SEEDS = g['GEN'], g['SEEDS']

OPC = {'ADD': 0x01, 'MUL': 0x02, 'SUB': 0x03, 'DIV': 0x04, 'SDIV': 0x05, 'MOD': 0x06, 'SMOD': 0x07, 'ADDMOD': 0x08,
       'MULMOD': 0x09, 'EXP': 0x0a, 'SIGNEXTEND': 0x0b, 'LT': 0x10, 'GT': 0x11, 'SLT': 0x12, 'SGT': 0x13, 'EQ': 0x14,
       'ISZERO': 0x15, 'BYTE': 0x1a, 'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
TABLE = {'SDIV', 'MOD', 'SMOD', 'ADDMOD', 'EXP', 'BYTE'}
WIDTHS = (1, 2, 3, 4, 8, 20, 32)


def push(v, i):
    n = max(1, (v.bit_length() + 7) // 8)
    w = 32 if i % 3 == 0 else next(x for x in WIDTHS if x >= n)
    return bytes([0x5f + w]) + v.to_bytes(w, 'big')


def program(cases):
    code = b''
    for i, (op, a, b, c) in enumerate(cases):
        k = G.ARITY.get(op, 2)
        words = [a, b, c][:k]
        for j, v in enumerate(reversed(words)):
            code += push(v, i + j)
        code += bytes([OPC[op]])
    return code + b'\x00'


t = targets.get('geth-amd64')
fspec = gfaults.get(FAULT)
L = gloop.Loop(t['bin'], t['fns'], faults=fspec.get('faults'), text_patch=fspec.get('text_patch'))
res = {'target': 'geth-amd64 execUntraced', 'set': SET, 'shard': SHARD, 'nshard': NSHARD, 'fault': FAULT, 'faultWhere': fspec.get('where'),
       'seed': SEEDS.get(SET), 'K': K, 'cases': 0, 'mismatches': 0, 'errors': 0, 'programs': 0, 'steps': 0,
       'byOp': {}, 'byTag': {}, 'records': []}
t0 = time.time()


def run_batch(batch):
    cases = [x[2:] for x in batch]
    try:
        words, st, steps, gas, cpu = L.run(program(cases))
        res['steps'] += steps; res['programs'] += 1
        if st != 'stop' or len(words) != len(cases):
            raise gloop.Stop('status %s, %d words for %d cases' % (st, len(words), len(cases)))
    except Exception as e:
        if len(batch) == 1:
            k, tag, op, a, b, c = batch[0]
            res['errors'] += 1; res['byOp'][op][2] += 1
            res['records'].append({'index': k, 'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': '%s: %s' % (type(e).__name__, e)})
            return
        for x in batch:
            run_batch([x])
        return
    for (k, tag, op, a, b, c), got in zip(batch, words):
        want = G.ref(op, a, b, c)
        if got != want:
            res['mismatches'] += 1; res['byOp'][op][1] += 1
            res['records'].append({'index': k, 'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'model': hex(got), 'reference': hex(want)})


batch = []
for k, (tag, op, a, b, c) in enumerate(GEN[SET]()):
    if k % NSHARD != SHARD or op not in OPC:
        continue
    if fspec.get('ops') and op not in fspec['ops']:
        continue
    st = res['byOp'].setdefault(op, [0, 0, 0]); st[0] += 1; res['cases'] += 1
    res['byTag'][tag] = res['byTag'].get(tag, 0) + 1
    batch.append((k, tag, op, a, b, c))
    if len(batch) == K:
        run_batch(batch); batch = []
        if fspec.get('stop_after') and res['mismatches'] >= fspec['stop_after']:
            break
if batch:
    run_batch(batch)
res['seconds'] = time.time() - t0
res['visited'] = len(L.visited)
res['inlineOps'] = sorted(set(res['byOp']) - TABLE); res['tableOps'] = sorted(set(res['byOp']) & TABLE)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'programs', res['programs'], 'steps', res['steps'], flush=True)
