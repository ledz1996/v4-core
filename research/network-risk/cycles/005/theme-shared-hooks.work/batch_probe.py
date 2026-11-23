import sys, json, collections
from lib import *
from summ import load, flags, census
from probe import probe
EXTRA = {4663: ['0x4e3468951d49f2eea976ed0d6e75ffcb44a9a544', '0x2c668601193e4a081dd82604785e436aff6a2acc'], 99901: ['0x6b1216a40b65c83e9c9e18a562c446697b8cf8ec'], 196: ['0x630e9cac0fff557bd3a01daa111ed253c771bcc0'], 143: ['0x94f802a9efe4dd542fdbd77a25d9e69a6dc828cc', '0x580ca49389d83b019d07e17e99454f2f218e2dc0']}
cid = int(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
cnt0, _, rows, total, cov = census(cid)
cnt = collections.Counter({h: c for h, c in cnt0.items() if int(h, 16)})
hs = [h for h, _ in cnt.most_common(N)]
for h in EXTRA.get(cid, []):
    if h not in hs: hs.append(h)
print('#### %d %s: pools %d, with hook %d, distinct hooks %d' % (cid, net(cid)['name'], total, sum(cnt.values()), len(cnt)), flush=True)
for h in hs:
    try: probe(cid, h)
    except Exception as e: print('   probe failed', h, repr(e)[:200])
    sys.stdout.flush()
