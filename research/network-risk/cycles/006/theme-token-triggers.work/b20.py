# Base: B20 tokens (addresses starting 0xb2) are precompiles without a selector table in code. The function list is taken
# from the canonical interfaces in base/base-std (IB20, IB20Asset, IB20Stablecoin, IERC8056) and used for the step 2 trials.
import json, gzip, os, re, shutil, sys
from base import *
import sweep, slots
ENUM = {'PausableFeature': 'uint8', 'IB20.PausableFeature': 'uint8'}
sigs = []
for f in ('IB20', 'IB20Asset', 'IB20Stablecoin', 'IERC8056'):
    src = open(os.path.join(RAW6, 'b20', f + '.sol')).read()
    src = re.sub(r'//.*', '', src)
    for m in re.finditer(r'function\s+(\w+)\s*\(([^)]*)\)\s*external([^;{]*)', src):
        name, args, tail = m.group(1), m.group(2), m.group(3)
        types = []
        for a in [x.strip() for x in args.split(',') if x.strip()]:
            t = a.split()[0]
            arr = ''
            while t.endswith('[]'): t = t[:-2]; arr += '[]'
            t = ENUM.get(t, t)
            types.append(t + arr)
        sigs.append((name + '(' + ','.join(types) + ')', 'view' in tail or 'pure' in tail))
sigs = sorted(set(sigs))
print(len(sigs), 'functions;', 'state changing:', [s for s, v in sigs if not v])
if '--list' in sys.argv: sys.exit()
for s, v in sigs:
    if not v: sweep.SIG[sel(s)[2:]] = [s]
sweep.TRIG = re.compile('.')
cid = 8453
real = os.path.join(RAW6, 'discover_%d.json.gz' % cid); d = jz(real)
b20 = {t: o for t, o in d.items() if t.startswith('0xb2000000')}
for t, o in b20.items(): o['sels'] = [sel(s)[2:] for s, v in sigs if not v]
shutil.copy(real, real + '.main'); sreal = os.path.join(RAW6, 'slots_%d.json.gz' % cid); shutil.copy(sreal, sreal + '.main')
try:
    json.dump(b20, gzip.open(real, 'wt'))
    slots.run(cid)
    for md in 'ABC':
        sweep.run(cid, mode=md)
        fn = os.path.join(RAW6, 'sweep%s_%d.json.gz' % ('' if md == 'A' else md, cid))
        os.replace(fn, os.path.join(RAW6, 'b20_sweep%s_%d.json.gz' % (md, cid)))
finally:
    shutil.move(real + '.main', real); shutil.move(sreal + '.main', sreal)
