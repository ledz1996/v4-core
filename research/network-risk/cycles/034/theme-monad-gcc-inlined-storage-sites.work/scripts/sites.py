"""Cycle 34, Task 1: the KECCAK256, SLOAD, SSTORE, TLOAD, TSTORE and LOG sites of the 128 value-computing PoolManager
blocks without a mined run since v0.16.7 (cycle 31 out/value128-ops.json, out/states.jsonl), each mapped to src/ through
the solc source map (cycle 12 srcmap.py). usage: python3 -I sites.py <out.json>"""
import sys, json, os
R = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, R + '/cycles/012/theme-bytecode-coverage.work'); sys.path.insert(0, R + '/cycles/031/theme-monad-gcc-real-states.work/scripts')
import srcmap
from blockops import opname
code = bytes.fromhex(open(R + '/cycles/027/theme-monad-engine-agreement.work/out/pm-runtime.hex').read().strip().removeprefix('0x'))
DIFF = [i for i in range(len(code)) if code[i] != srcmap.code[i]]
# the two runtimes differ only in one 20-byte immutable (the PoolManager's own address), which moves no instruction
assert len(code) == len(srcmap.code) == 24009 and len(DIFF) == 20 and DIFF[-1] - DIFF[0] == 19, DIFF[:4]
states = [json.loads(l) for l in open(R + '/cycles/031/theme-monad-gcc-real-states.work/out/states.jsonl')]
want = {int(k, 16) for k in json.load(open(R + '/cycles/031/theme-monad-gcc-real-states.work/out/value128-ops.json'))['blocks']}
KINDS = {'KECCAK256', 'SHA3', 'SLOAD', 'SSTORE', 'TLOAD', 'TSTORE', 'LOG0', 'LOG1', 'LOG2', 'LOG3', 'LOG4'}
out = []
for i, s in enumerate(states):
    if s['w'] == 'i' and s['b'] in want and opname(s['pc']) in KINDS:
        L = srcmap.loc(s['pc'])
        top = s['elems'][-1] if s['elems'] else {}
        ctx = []
        # compiler-generated code maps to the contract (PoolManager.sol:80); name the nearest specific lines in the block
        j = i - 1
        while j >= 0 and states[j]['b'] == s['b'] and len(ctx) < 2:
            if states[j]['w'] == 'i':
                l2 = srcmap.loc(states[j]['pc'])
                if l2['line'] and not (l2['file'] == 'src/PoolManager.sol' and l2['line'] == 80) and (l2['file'], l2['line']) not in [(a, b) for a, b, _ in ctx]:
                    ctx.append((l2['file'], l2['line'], l2['snippet'][:90]))
            j -= 1
        out.append({'block': hex(s['b']), 'pc': hex(s['pc']), 'op': opname(s['pc']), 'stateIndex': i, 'file': L['file'], 'line': L['line'],
                    'endLine': L.get('endLine'), 'snippet': L['snippet'],
                    'keyLiteral': top.get('lit'), 'precedingSourceInBlock': ctx})
def cls(r):
    f = r['file'] or ''
    if any(x in f for x in ('CurrencyDelta', 'NonzeroDeltaCount', 'Lock.sol', 'CurrencyReserves')): return 0
    if r['op'] in ('SSTORE', 'SLOAD', 'TLOAD', 'TSTORE') and 'Pool.sol' in f: return 1
    if r['op'] in ('SSTORE', 'SLOAD', 'TLOAD', 'TSTORE'): return 2
    if r['op'] in ('KECCAK256', 'SHA3'): return 3
    return 4
for r in out: r['group'] = ['transient-lock-delta-count-reserves', 'pool-state', 'other-storage', 'hashing', 'logs'][cls(r)]
out.sort(key=lambda r: (cls(r), r['file'] or '', r['line'] or 0, int(r['pc'], 16)))
cnt = {}
for r in out: cnt[r['op']] = cnt.get(r['op'], 0) + 1
json.dump({'counts': cnt, 'sites': out}, open(sys.argv[1], 'w'), indent=1)
print(cnt, len(out))
for r in out: print(r['group'], r['block'], r['pc'], r['op'], r['file'], r['line'], r['snippet'][:50], (r['keyLiteral'] or '')[-6:], r['precedingSourceInBlock'][:1])
