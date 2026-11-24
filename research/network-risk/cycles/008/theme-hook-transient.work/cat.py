from srcget import *
j = fetch(int(sys.argv[1]), sys.argv[2]); pat = sys.argv[3]
lo = int(sys.argv[4]) if len(sys.argv) > 4 else 1; hi = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
for name, s in j['sources'].items():
    if name.endswith(pat):
        for i, l in enumerate(s['content'].split('\n')):
            if lo <= i + 1 <= hi: print('%4d  %s' % (i + 1, l.rstrip()[:230]))
