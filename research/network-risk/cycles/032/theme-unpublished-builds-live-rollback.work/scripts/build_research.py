"""Aggregate the outputs of this unit by the build that answered and write the research file."""
import json, glob, os, collections
W = '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.work'
OUT = '/home/user/v4-core/research/network-risk/cycles/032/theme-unpublished-builds-live-rollback.research.json'
def J(p): return json.load(open(os.path.join(W, p)))
def bname(v, chain):
    c = (v.get('web3_clientVersion') or {}).get('result') or 'refused'
    if chain == 5042: c += ' arc ' + ((v.get('arc_getVersion') or {}).get('result') or {}).get('git_short_hash', '?')
    return c.split('@')[0] if 'mega-reth' in c else c
tally = collections.defaultdict(lambda: collections.Counter())
mism = []
# nested
for f in glob.glob(W + '/out/nested_*.json'):
    for r in json.load(open(f)):
        b0, b1 = bname(r['before'], r['chain']), bname(r['after'], r['chain'])
        key = (r['chain'], b0 if b0 == b1 else b0 + ' / ' + b1, r['url'])
        for c in r['cases']:
            if isinstance(c['node'], dict): tally[key]['refused'] += 1
            else:
                tally[key]['nested'] += 1
                if not c['equal']: mism.append(('nested', r['url'], c))
# token probe
for f in glob.glob(W + '/out/tok_*.json'):
    for r in json.load(open(f)):
        b0, b1 = bname(r['before'], r['chain']), bname(r['after'], r['chain'])
        key = (r['chain'], b0 if b0 == b1 else b0 + ' / ' + b1, r['url'])
        for c in r['cases']:
            if 'rows' in c:
                tally[key]['tokenProbe'] += 1
                if c['leaks'] or not c['controlMoved'] or not c['staticRefused']: mism.append(('tok', r['url'], c['label']))
            if c.get('simTransferLogs') is not None: tally[key]['logCheckSimulate'] += 1
            if c.get('traceTransferLogs') is not None: tally[key]['logCheckTrace'] += 1
# arcpin
ap = J('out/arcpin.json')
for u, e in ap['endpoints'].items():
    for b, d in e['byBuild'].items():
        tally[(5042, 'arc ' + b, u)]['arcPinned'] += d['runs']
        if d['ok'] != d['runs']: mism.append(('arcpin', u, b))
# unlock
nets = {5042: 'unlock_5042_*', 99901: 'unlock_99901_*', 999: 'unlock_999_*', 4326: 'unlock_4326_*', 56: 'unlock_56_*'}
for ch, pat in nets.items():
    for f in glob.glob(W + '/out/' + pat + '.json'):
        d = json.load(open(f)); b0, b1 = d['clientBefore'].get('result'), d['clientAfter'].get('result')
        key = (ch, b0 if b0 == b1 else b0 + ' / ' + b1, d['url'])
        for v in d['variants'].values():
            tally[key]['unlock'] += 1
            if not v['equal']: mism.append(('unlock', d['url'], v))
# txreset
for f in glob.glob(W + '/out/txreset_*.json'):
    ch = int(f.split('_')[-1].split('.')[0])
    for r in json.load(open(f)):
        b0, b1 = bname(r['before'], ch), bname(r['after'], ch)
        key = (ch, b0 if b0 == b1 else b0 + ' / ' + b1, r['url'])
        if 'reads' in r:
            tally[key]['txReset'] += 1
            if not r['ok']: mism.append(('txreset', r['url']))
        else: tally[key]['txResetRefused'] += 1
# pinned script sets
for f in glob.glob(W + '/out/pinned/pinned_*.json'):
    d = json.load(open(f)); tag = f.split('pinned_')[-1][:-5]
    bs = sorted({bname(r[s], d['chain']) for r in d['runs'].values() for s in ('before', 'after')})
    key = (d['chain'], ' / '.join(bs), d['url'])
    p1 = J(f'out/pinned/pm1_{tag}.json')['results'][0]; p2 = J(f'out/pinned/pm2_{tag}.json')['results'][0]
    br = J(f'out/pinned/borrow_{tag}.json')
    tally[key]['pmdiff'] += p1['identical']; tally[key]['pmdiffDifferent'] += len(p1['different'])
    tally[key]['pmdiff2'] += p2['identical']; tally[key]['pmdiff2Different'] += len(p2['different'])
    tally[key]['pmdiff2DiffScripts'] = 0
    if p2['different']: tally[key]['pmdiff2DiffScript189'] += (p2['different'] == [189])
    s = json.dumps(br)
    tally[key]['borrowScripts'] += 3
    if p1['different'] or (p2['different'] and p2['different'] != [189]): mism.append(('pinned', d['url'], p1['different'], p2['different']))
rows = [{'chain': k[0], 'build': k[1], 'url': k[2], **{a: b for a, b in v.items() if b}} for k, v in sorted(tally.items())]
json.dump({'tally': rows, 'mismatches': mism}, open(W + '/out/tally.json', 'w'), indent=1)
for r in rows: print(r)
print('MISMATCHES', mism)
