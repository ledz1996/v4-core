"""Per PoolManager instruction: classes seen in validated MegaETH blocks (agg files) and in HyperEVM replica traces."""
import json, sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classes import NAMES, OPS
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
inv = json.load(open(os.path.join(W, 'out/pm-inventory.json')))
mega = {}
for f in sys.argv[1:]:
    if '999' in f: continue
    for k, v in json.load(open(f))['pm'].items():
        op, c, pc = map(int, k.split(':'))
        e = mega.setdefault((pc, c), {'occ': 0, 'nblocks': 0, 'first': v['first'], 'last': v['last'], 'example': v['example']})
        e['occ'] += v['occ']; e['nblocks'] += v['nblocks']; e['first'] = min(e['first'], v['first'])
        if v['last'] >= e['last']: e['last'] = v['last']; e['example'] = v['example']
hyp = {}
for f in sys.argv[1:]:
    if '999' not in f: continue
    for k, v in json.load(open(f))['pm'].items():
        op, c, pc = map(int, k.split(':'))
        hyp[(pc, c)] = v
rows = []
for x in inv:
    pc = x['pc']
    cl = sorted({c for (p, c) in list(mega) + list(hyp) if p == pc})
    rows.append({'pc': pc, 'op': x['op'], 'file': x['src'].get('file'), 'line': x['src'].get('line'), 'snippet': x['src'].get('snippet', '')[:90],
                 'mega': {NAMES[(x['opn'], c)]: [mega[(pc, c)]['occ'], mega[(pc, c)]['nblocks'], mega[(pc, c)]['last']] for c in cl if (pc, c) in mega},
                 'hyper': {NAMES[(x['opn'], c)]: [hyp[(pc, c)]['occ'], hyp[(pc, c)]['txs'], hyp[(pc, c)]['exampleTx']] for c in cl if (pc, c) in hyp}})
json.dump(rows, open(os.path.join(W, 'out/pm-sites.json'), 'w'), indent=1)
for r in rows:
    if r['op'] in ('SHR', 'SHL', 'SLT', 'SGT', 'SIGNEXTEND') and '-v' not in os.environ.get('V', ''): continue
    print(r['pc'], r['op'], r['file'], r['line'], {k[-30:]: v[:2] for k, v in r['mega'].items()}, '|', {k[-30:]: v[:2] for k, v in r['hyper'].items()})
