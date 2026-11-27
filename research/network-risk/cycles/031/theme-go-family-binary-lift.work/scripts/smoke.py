"""Quick timing and sanity run of the models. usage: python3 -I smoke.py <arch> <n> [handler|direct]"""
import os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models, goshim as G, targets
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TGT = sys.argv[1]; arch = TGT.split('-')[1]; N = int(sys.argv[2]); mode = sys.argv[3] if len(sys.argv) > 3 else 'handler'
m = targets.model(TGT)
print('missing', m.missing, 'stops', {hex(a): n for a, n in m.stops.items()}, flush=True)
rnd = random.Random(1)
ops = list(G.HANDLERS) if mode == 'handler' else list(G.DIRECT)
for op in ops:
    t = time.time(); n = 0; st = 0; bad = 0
    for i in range(N):
        a, b, c = rnd.getrandbits(256), rnd.getrandbits(256), rnd.getrandbits(rnd.choice((64, 128, 200, 256)))
        if op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR'): a = rnd.randrange(300)
        try:
            got, steps = (m.run_handler if mode == 'handler' else m.run_direct)(op, a, b, c)
        except Exception as e:
            print(op, 'ERR', type(e).__name__, e, flush=True); break
        n += 1; st += steps
        if got != G.ref(op, a, b, c): bad += 1
    dt = time.time() - t
    print(op, n, 'bad', bad, 'steps/call', st // max(n, 1), 'calls/s %.0f' % (n / dt), 'steps/s %.0f' % (st / dt), flush=True)
