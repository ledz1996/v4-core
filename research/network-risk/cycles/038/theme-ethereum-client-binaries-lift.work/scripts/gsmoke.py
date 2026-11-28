"""Smoke test of gloop: a few programs through execUntraced."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gloop, targets
t = targets.get('geth-amd64')
L = gloop.Loop(t['bin'], t['fns'])
def p32(v): return b'\x7f' + v.to_bytes(32, 'big')
a, b = 7, 1 << 200
for name, code in [('add', p32(b) + p32(a) + b'\x01\x00'), ('div', p32(a) + p32(b) + b'\x04\x00'), ('sdiv', p32(3) + p32(b) + b'\x05\x00'), ('shl', p32(1) + p32(5) + b'\x1b\x00'), ('end', p32(1) + p32(5) + b'\x1b')]:
    t0 = time.time()
    try:
        words, st, steps, gas, cpu = L.run(code)
        print(name, st, [hex(x) for x in words], steps, gas, '%.2fs' % (time.time() - t0))
    except Exception as e:
        print(name, 'ERR', type(e).__name__, e)
