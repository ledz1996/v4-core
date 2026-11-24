import json, sys
from collections import Counter
for f in sys.argv[1:]:
    R = json.load(open(f))['results']; cid = json.load(open(f))['chainId']
    C = [r for r in R if 'result' in r]
    nat = [r for r in C if 'native' in r]
    agree = sum(1 for r in nat for c, v in r['currencies'].items() if int(c, 16) == 0 and int(r['native']['balanceDiff']) == -(int(v['out']) - int(v['in'])))
    agree_alone = sum(1 for r in nat if not r['native']['otherPmTxInBlock'] for c, v in r['currencies'].items() if int(c, 16) == 0 and int(r['native']['balanceDiff']) == -(int(v['out']) - int(v['in'])))
    alone = sum(1 for r in nat if not r['native']['otherPmTxInBlock'])
    via = Counter(r['native']['via'] for r in nat)
    feesnz = sum(1 for r in C for e in r['detail'] if 'fees' in e and any(int(x) for x in e['fees']))
    paidunits = sum(1 for r in C for v in r['currencies'].values() if int(v['out']) > 0)
    print(cid, 'checked tx', len(C), 'results', dict(Counter(r['result'] for r in C)), 'kinds', dict(Counter(r['kind'] for r in C)),
          'removal events', sum(r['removals'] for r in C), 'collect events', sum(r['collects'] for r in C), 'events with fees>0', feesnz,
          'currency legs paid', paidunits, 'storage mismatch', sum(1 for r in C if r['storageMismatch']),
          'native legs', len(nat), dict(via), 'balance agrees', agree, 'alone in block', alone, 'agree alone', agree_alone,
          'aside', dict(Counter(r.get('aside') for r in R if r.get('aside'))), 'errors', sum(1 for r in R if 'error' in r), 'blocks', (min(r['block'] for r in R), max(r['block'] for r in R)))
