"""Combines the per-run aggregates into out/summary-megaeth.json (class table with example transaction),
out/pm-unexecuted-megaeth.json (Task 2) and prints both. Read-only RPC to resolve example transactions."""
import json, os, sys, glob, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classes import NAMES, OPS
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = 'https://mainnet.megaeth.com/rpc'
runs = [r for r in ('pm911', 'pmnew', 'newest20k', 'pmrest') if os.path.exists(os.path.join(W, 'out/agg-%s.json' % r))]
A = {r: json.load(open(os.path.join(W, 'out/agg-%s.json' % r))) for r in runs}
def rpc(m, p):
    q = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(R, q, {'content-type': 'application/json', 'user-agent': 'census-readonly'}), timeout=120).read())
summ = {'runs': {r: {k: A[r][k] for k in ('listed', 'validated', 'notValidated', 'clientBefore', 'clientAfter')} for r in runs}, 'classes': {}}
summ['clientBefore'] = rpc('web3_clientVersion', [])['result']
for k in sorted(NAMES):
    s = '%d:%d' % k
    e = {'name': NAMES[k], 'occ': 0, 'blocks': 0, 'first': None, 'last': None, 'contractsPerRun': {}, 'example': None}
    for r in runs:
        v = A[r]['classes'].get(s)
        if not v: continue
        e['occ'] += v['occ']; e['blocks'] += v['nblocks']; e['contractsPerRun'][r] = v['ncontracts']
        e['first'] = v['first'] if e['first'] is None else min(e['first'], v['first'])
        if e['last'] is None or v['last'] >= e['last']: e['last'] = v['last']; e['example'] = v['example']
    if e['example'] and k[1] != 0:
        ex = e['example']
        b = rpc('eth_getBlockByNumber', [hex(ex['block']), True])['result']
        m = [t['hash'] for t in b['transactions'] if t['from'].lower() == ex['origin'].lower()]
        ex['txCandidates'] = m
    summ['classes'][s] = e
summ['clientAfter'] = rpc('web3_clientVersion', [])['result']
json.dump(summ, open(os.path.join(W, 'out/summary-megaeth.json'), 'w'), indent=1)
# Task 2
inv = json.load(open(os.path.join(W, 'out/pm-inventory.json')))
seen = {}
for r in runs:
    for kk, v in A[r]['pm'].items():
        op, c, pc = map(int, kk.split(':'))
        e = seen.setdefault((pc, c), {'occ': 0, 'last': 0}); e['occ'] += v['occ']; e['last'] = max(e['last'], v['last'])
REL = {'MULMOD': [1, 2], 'SDIV': [1, 2], 'SMOD': [1, 2], 'SAR': [1], 'SIGNEXTEND': [1, 2], 'SLT': [1, 2], 'SGT': [1, 2], 'BYTE': [1, 2],
       'SHL': [1], 'SHR': [1], 'DIV': [1], 'MOD': [1]}
rows = []
for x in inv:
    pc = x['pc']; ex = (pc, 0) in seen
    for c in REL[x['op']]:
        if (pc, c) not in seen:
            rows.append({'pc': pc, 'op': x['op'], 'class': NAMES[(x['opn'], c)], 'instructionExecuted': ex,
                         'execCount': seen.get((pc, 0), {}).get('occ', 0), 'src': '%s:%s' % (x['src'].get('file'), x['src'].get('line')),
                         'snippet': x['src'].get('snippet', '')[:100]})
json.dump(rows, open(os.path.join(W, 'out/pm-unexecuted-megaeth.json'), 'w'), indent=1)
for k, e in summ['classes'].items():
    print(e['name'][:58].ljust(58), e['occ'], e['blocks'], e['first'], e['last'], (e['example'] or {}).get('txCandidates'))
import collections
print(len(rows), collections.Counter((r['op'], r['class'], r['instructionExecuted']) for r in rows))
