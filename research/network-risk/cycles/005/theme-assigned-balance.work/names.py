import json, gzip, glob, os, re, collections
RAW = 'raw'
SIG = json.load(gzip.open(os.path.join(RAW, 'signatures.json.gz')))
CIDS = [1, 10, 8453, 130, 7777777, 480, 57073, 1868, 42220, 196, 42161, 4663, 99901, 137, 56, 43114, 143, 4326, 4217, 5042, 999]
def load(cid):
    f1 = os.path.join(RAW, 'codehash_%d.json.gz' % cid); f2 = os.path.join(RAW, 'selectors_%d.json.gz' % cid)
    if not (os.path.exists(f1) and os.path.exists(f2)): return {}, {}
    return json.load(gzip.open(f1)), json.load(gzip.open(f2))
def names_of(p):
    out = []
    for s in p['sels']:
        for nm in SIG.get(s) or []: out.append((s, nm))
    return out
