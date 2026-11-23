# Print one source file of a fetched verified contract with line numbers. usage: show.py <cid> <addr> <file substring> [from] [to]
import sys
from common import *
cid, h, pat = int(sys.argv[1]), sys.argv[2].lower(), sys.argv[3]
a = int(sys.argv[4]) if len(sys.argv) > 4 else 1; b = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 9
for d in (RAW, os.path.join(C5, 'raw')):
    try: j = json.load(open(os.path.join(d, 'src', '%d_%s.json' % (cid, h)))); break
    except Exception: j = None
for k, v in j['sources'].items():
    if pat in k:
        L = v['content'].split('\n')
        print('==', k, len(L), 'lines', j.get('_from'))
        for i, l in enumerate(L):
            if a <= i + 1 <= b: print('%4d %s' % (i + 1, l[:230]))
