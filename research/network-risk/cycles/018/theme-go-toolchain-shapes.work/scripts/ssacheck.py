#!/usr/bin/env python3
"""Compile one function with the installed Go (go1.24.7, NOT an affected compiler) under GOSSAFUNC and
report, from ssa.html, whether branchelim turned a Phi of pointer type into a CondSelect, and which
values the CondSelect feeds (Store/Zero/Move address = the 81863 precondition).
Usage: ssacheck.py <pkgdir> <GOSSAFUNC name> <outdir>"""
import html, os, re, subprocess, sys
pkg, fn, out = sys.argv[1:4]
out = os.path.abspath(out); os.makedirs(out, exist_ok=True)
env = dict(os.environ, GOSSAFUNC=fn, GOSSADIR=out, GOFLAGS='-mod=mod', GOTOOLCHAIN='local')
r = subprocess.run(['go', 'build', '-o', os.devnull, '.'], cwd=pkg, env=env, capture_output=True, text=True)
files = [os.path.join(d, f) for d, _, fs in os.walk(out) for f in fs if f.endswith('.html')]
if not files:
    print('no ssa.html', r.stderr[-400:]); sys.exit(1)
for f in sorted(files):
    t = open(f).read()
    cols = re.split(r'<td id="', t)
    for c in cols[1:]:
        name = c.split('"')[0]
        if 'branchelim' not in name or not name.endswith('-exp'):
            continue
        txt = html.unescape(re.sub(r'<[^>]+>', '\n', c))
        vals = re.findall(r'(v\d+) \([^)]*\) = (\w+) <([^>]*)> ?([^\n]*)', txt)
        cs = [(v, ty, rest) for v, op, ty, rest in vals if op == 'CondSelect']
        print(os.path.basename(f), 'CondSelect count', len(cs))
        for v, ty, rest in cs:
            users = [(u, op, a) for u, op, _, a in vals if re.search(r'\b%s\b' % v, a)]
            print('  ', v, ty, rest.strip(), '-> users', users)
        phis = [(v, ty, rest) for v, op, ty, rest in vals if op == 'Phi' and ty.startswith('*')]
        print('  pointer Phis kept:', phis)
