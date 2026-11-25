"""Debug: rerun one mismatched group of v3check.py with one fee and print the loop's result next to the log. Read only.
Usage: dbg3.py <pool> <block> <fee>"""
import sys
ARGS = (sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
sys.argv = ['v3check.py', 'raw/_dbg.json']
exec(open('v3check.py').read().split('t0 = time.time(); n = 0')[0])
pool, block, fee = ARGS
rows = [r for r in ev[pool] if r[1] == block]; print("rows", len(rows), len(ev[pool]))
s0, lq = batch([(pool, '0x3850c7bd', block - 1), (pool, '0x1a686502', block - 1)])
p = int(s0[2:66], 16); t_raw = int(s0[66:130], 16); tick = t_raw - (1 << 256) if t_raw >> 255 else t_raw; liq = int(lq, 16)
view = View(pool, block, pools[pool]['tickSpacing'])
for r in rows:
    print('log', r)
    if r[0] != 'S': continue
    a0, a1, p1, L1, t1 = r[5:10]; zfo = p1 < p; paid, got = expect(zfo, a0, a1)
    edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
    for f in (fee - 1, fee, fee + 1):
        try: print(f, 'in', loop(view, p, tick, liq, zfo, -paid, edge, f), 'want', (p1, t1, L1, paid, got))
        except Exception as e: print(f, 'err', e)
        try: print(f, 'out', loop(view, p, tick, liq, zfo, got, edge, f))
        except Exception as e: print(f, 'err', e)
    print('slot0 words', [int(s0[2 + 64 * i:66 + 64 * i], 16) for i in range(7)])
    p, tick, liq = p1, t1, L1
