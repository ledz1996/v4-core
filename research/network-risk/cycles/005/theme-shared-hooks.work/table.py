import json, glob, sys, collections
from summ import flags
from lib import *
order = [n['chainId'] for n in NETS]
P = [json.load(open(f)) for f in glob.glob('raw/probe/[0-9]*.json')]
P.sort(key=lambda p: (order.index(p['chainId']), -p['pools']))
for p in P:
    if len(sys.argv) > 1 and str(p['chainId']) not in sys.argv[1:]: continue
    oks = [i['variant'].split(' fee')[0].split(' dynamic')[0][:14] + ('(dyn)' if 'dynamic' in i['variant'] else '') for i in p['init'] if i['ok']]
    bad = collections.Counter(i['result'].split(': ', 1)[-1][:40].rstrip(')') for i in p['init'] if not i['ok'])
    init = ('OPEN ' + ('all' if len(oks) == len(p['init']) else '|'.join(oks))) if oks else 'GATED'
    if bad: init += ' / rej: ' + '; '.join('%s x%d' % kv for kv in bad.items())
    cbs = '; '.join('%s%s=%s' % (c['fn'].replace('before', 'b').replace('after', 'a').replace('Liquidity', 'L').replace('Remove', 'R').replace('Add', 'A'), '' , ('ok' + ((' Δ!' + c['result'].split('ret1=')[1]) if 'ret1=' in c['result'] and c['result'].split('ret1=')[1].replace('ret2=', '').strip() else '')) if c['ok'] else c['result'][:34]) for c in p['callbacks'] if c['key'] == p['callbacks'][0]['key'])
    print('%-8d %s n=%-6d len=%-5d %s %s [%s]\n      init: %s\n      cb(%s): %s' % (p['chainId'], p['hook'], p['pools'], p['codeLen'], p['codeHash'][:8], (p.get('proxy1167') or p.get('impl1967') or ''), ','.join(flags(p['hook'])), init, p['callbacks'][0]['key'][:12] if p['callbacks'] else '-', cbs))
