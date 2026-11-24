"""Step by step: the trace a network returns for a script (debug_traceCall with the
same state override as pmdiff) against the trace of the reference interpreter. For
every step the depth, the program counter and the opcode must agree, and the top
four stack words must agree except where a word comes from the GAS opcode, which the
reference does not model. Of the public endpoints only Tempo's serves traces.

Usage: python3 trace.py <out.json> [nScripts per set] [rpc url]
"""
import sys, json, random, time
from evm import rpc
import pmdiff as P, pmdiff2 as Q
from pyevm import World, NAMES
from bytecode import worlds

GASV = 10 ** 9


def compare(url, ov, data, mk, max_steps):
    w = mk(); w.trace = []; w.trace_stack = 4; w.max_steps = max_steps
    try:
        w.call(0, int(P.DRV, 16), 0, data, False, 0)
    except TimeoutError:
        return {'skipped': 'heavy'}
    r = None
    for k in range(5):
        try:
            r = rpc(url, 'debug_traceCall', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(25_000_000)}, 'latest',
                                             {'stateOverrides': ov, 'disableStorage': True, 'enableMemory': False}], timeout=300); break
        except Exception as e:  # noqa
            err = str(e)[:100]; time.sleep(3 * (k + 1))
    if r is None: return {'error': err}
    logs = r['structLogs']
    if len(logs) != len(w.trace): return {'steps': len(logs), 'reference': len(w.trace), 'difference': 'length'}
    for i, (a, (d, pc, op, stk)) in enumerate(zip(logs, w.trace)):
        if a['pc'] != pc or a['op'] != NAMES[op] or a['depth'] != d + 1:
            return {'steps': len(logs), 'difference': [i, a['pc'], a['op'], a['depth'], pc, NAMES[op], d + 1]}
        top = [int(x, 16) for x in a['stack'][-4:]]
        if len(top) != len(stk) or any(x != y and y != GASV for x, y in zip(top, stk)):
            return {'steps': len(logs), 'difference': [i, 'stack', a['stack'][-4:], [hex(x) for x in stk]]}
    return {'steps': len(logs)}


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    url = sys.argv[3] if len(sys.argv) > 3 else 'https://rpc.mainnet.tempo.xyz'
    code = P.fetch_code(); w1, w2 = worlds(code)
    rnd = random.Random(7_2026_11_24); s1 = [P.script(rnd) for _ in range(250)]
    rnd = random.Random(11_2026_11_24); s2 = [Q.script(rnd, i) for i in range(300)]
    ov1 = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + P.driver().hex()}}
    ov2 = {P.PM: {'code': '0x' + code.hex(), 'balance': hex(10 ** 19)}, P.DRV: {'code': '0x' + Q.driver().hex()}, '0x' + Q.TOKEN.to_bytes(20, 'big').hex(): {'code': '0x' + Q.token().hex()}}
    for f in Q.HOOK_FLAGS: ov2['0x' + (Q.HOOK_BASE | f).to_bytes(20, 'big').hex()] = {'code': '0x' + Q.hook().hex()}
    res = []; tot = {'scripts': 0, 'identical': 0, 'steps': 0, 'different': 0, 'skipped': 0, 'errors': 0}
    for name, scripts, ov, mk in (('pmdiff', s1, ov1, w1), ('pmdiff2', s2, ov2, w2)):
        for i in range(min(n, len(scripts))):
            r = compare(url, ov, scripts[i][0], mk, 400_000); r.update(set=name, script=i); res.append(r)
            tot['scripts'] += 1
            if 'skipped' in r: tot['skipped'] += 1
            elif 'error' in r: tot['errors'] += 1
            elif 'difference' in r: tot['different'] += 1; print('DIFFERENT', r)
            else: tot['identical'] += 1; tot['steps'] += r['steps']
    print(tot)
    json.dump({'rpc': url, 'totals': tot, 'results': res}, open(out, 'w'), indent=1)
