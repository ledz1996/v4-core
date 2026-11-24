from srcget import *
EXC = re.compile(r'(Lock|CurrencyDelta|CurrencyReserves|NonzeroDeltaCount|TransientStateLibrary|Exttload|IExttload|IPoolManager|StateLibrary)\.sol$')
def show(cid, a, pat=r'tstore|tload|\btransient\b|Transient'):
    j = fetch(cid, a)
    if 'sources' not in j: print(cid, a, 'no source'); return
    print('##', cid, a, (j.get('compilation') or {}).get('name'), j.get('_from'))
    for name, s in j['sources'].items():
        if EXC.search(name): continue
        lines = s['content'].split('\n')
        for i, l in enumerate(lines):
            if re.search(pat, l) and not l.strip().startswith('//') and not l.strip().startswith('*') and not l.strip().startswith('///'): print('  %s:%d: %s' % (name.split('/')[-1], i + 1, l.strip()[:200]))
if __name__ == '__main__':
    for x in sys.argv[1:]:
        c, a = x.split(':'); show(int(c), a)
