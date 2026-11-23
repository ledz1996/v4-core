# Same as qtr.py but prints a compact list of the calls below PoolManager.swap: target, function, decoded address and amount arguments, error.
import sys
from common import *
import qtr
os.chdir(C5)
from sigs import lookup
os.chdir(HERE)
_n = {}
def nm(s):
    if s not in _n:
        try: _n.update(lookup([s]))
        except Exception: pass
        _n.setdefault(s, '')
    return (_n[s] or s).split('(')[0]
def walk(c, depth, out, maxd):
    inp = c.get('input', '0x'); s = inp[2:10]
    args = [inp[10 + 64 * i:10 + 64 * (i + 1)] for i in range(min(5, (len(inp) - 10) // 64))]
    def fmt(a):
        v = int(a, 16) if a else 0
        if v == 0: return '0'
        if a.startswith('000000000000000000000000') and v > 1 << 80: return '0x' + a[24:]
        if v > 1 << 255: return str(v - (1 << 256))
        return str(v) if v < 10 ** 30 else '0x' + a[:16] + '..'
    val = int(c.get('value', '0x0'), 16) if c.get('value') else 0
    out.append('%s%s %s.%s(%s)%s%s%s' % ('  ' * depth, c.get('type', '')[:1], c.get('to', '')[:12], nm(s) if s else '', ', '.join(fmt(a) for a in args), ' value=%d' % val if val else '', ' ERR=' + str(c.get('error'))[:40] + ' ' + (c.get('output') or '')[:74] if c.get('error') else '', ' -> ' + (c.get('output') or '')[2:66].lstrip('0')[:40] if c.get('type') == 'STATICCALL' and not c.get('error') else ''))
    if depth < maxd:
        for x in c.get('calls') or []: walk(x, depth + 1, out, maxd)
def find_swap(c):
    if c.get('input', '')[2:10] in ('f3cd914c',): return c
    for x in c.get('calls') or []:
        r = find_swap(x)
        if r: return r
def go(*a, maxd=5, **kw):
    r = qtr.run(*a, quiet=True, **kw)
    if not r: return None
    s = find_swap(r) or r
    out = []; walk(s, 0, out, maxd)
    print('\n'.join(l[:250] for l in out[:70]))
    print('top-level:', (r.get('error') or ''), (r.get('output') or '')[:140])
    return r
if __name__ == '__main__':
    a = sys.argv
    go(int(a[1]), a[2].lower(), a[3], a[4], int(a[5]), int(a[6]), int(a[7]), int(float(a[8])), a[9] if len(a) > 9 else 'in', (a[10] != '0') if len(a) > 10 else True, maxd=int(a[11]) if len(a) > 11 else 5)
