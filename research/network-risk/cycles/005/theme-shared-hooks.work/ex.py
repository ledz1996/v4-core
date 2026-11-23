# Extract the non-library source files of a fetched contract to a scratch directory for reading.
import sys, json, os
SP = '/tmp/claude-0/-home-user-v4-core/0b315df9-4a6b-5032-a881-24bad3c79fc5/scratchpad/src'
cid, addr = sys.argv[1], sys.argv[2].lower()
j = json.load(open('raw/src/%s_%s.json' % (cid, addr)))
d = os.path.join(SP, '%s_%s' % (cid, addr[:10])); os.makedirs(d, exist_ok=True)
for k, v in j['sources'].items():
    if any(x in k for x in ('openzeppelin', 'v4-core', 'solmate', 'forge-std', 'solady', 'permit2')) and len(sys.argv) < 4: continue
    fn = os.path.join(d, k.replace('/', '__'))
    open(fn, 'w').write(v['content']); print(fn, len(v['content'].split('\n')))
