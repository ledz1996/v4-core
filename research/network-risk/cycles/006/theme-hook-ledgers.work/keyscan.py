# For named hooks with verified source: print every state mapping and the body of beforeInitialize / _beforeInitialize.
import sys, re
from common import *
from srcscan import src, SKIPDIR
for arg in sys.argv[1:]:
    cid, h = arg.split(':'); cid = int(cid); j = src(cid, h.lower())
    if not j: print('##', arg, 'NO SOURCE'); continue
    name = (j.get('compilation') or {}).get('name'); print('##', arg, name, j.get('_from'))
    for k, v in j['sources'].items():
        if SKIPDIR.search(k) and k.split('/')[-1].split('.')[0] != name: continue
        L = v['content'].split('\n'); f = k.split('/')[-1]
        for i, l in enumerate(L):
            s = l.strip()
            if s.startswith('//') or s.startswith('*') or s.startswith('/*'): continue
            if re.match(r'mapping\s*\(', s) and re.search(r'uint|int|struct|=>\s*[A-Z]', s): print('  %s:%d: %s' % (f, i + 1, s[:150]))
            if re.search(r'function\s+_?beforeInitialize\b', l):
                body = []
                for jx in range(i, min(i + 22, len(L))):
                    t = L[jx].strip()
                    if t and not t.startswith('//'): body.append(t[:130])
                    if L[jx].startswith('    }'): break
                print('  %s:%d: %s' % (f, i + 1, ' '.join(body)[:700]))
