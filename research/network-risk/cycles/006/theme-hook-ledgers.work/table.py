# One line per candidate: holdings, flags, source name, initialize results, callback results.
import sys
from common import *
cand = json.load(open(os.path.join(RAW, 'cand.json')))
names = {}
for f in ['probe_all.log', 'probe_all_43114.log']:
    try:
        for l in open(os.path.join(RAW, f)):
            p = l.split(None, 2)
            if len(p) == 3 and not p[2].startswith('ERR'): names[(int(p[0]), p[1])] = p[2].strip()
    except Exception: pass
for c in cand:
    if len(sys.argv) > 1 and str(c['chainId']) not in sys.argv[1:]: continue
    p = {}
    for d in (RAW, os.path.join(C5, 'raw')):
        try: p = json.load(open(os.path.join(d, 'probe', '%d_%s.json' % (c['chainId'], c['hook'])))); break
        except Exception: pass
    if (c['chainId'], c['hook']) not in names:
        for d in (RAW, os.path.join(C5, 'raw')):
            try:
                sj = json.load(open(os.path.join(d, 'src', '%d_%s.json' % (c['chainId'], c['hook']))))
                if 'sources' in sj: names[(c['chainId'], c['hook'])] = (sj.get('compilation') or {}).get('name') or '?'; break
            except Exception: pass
    init = p.get('init', []); nok = sum(1 for i in init if i['ok'])
    errs = sorted(set(i['result'][:60] for i in init if not i['ok']))
    okv = [i['variant'][:14] for i in init if i['ok']]
    cbs = '; '.join('%s:%s' % (x['fn'].replace('before', 'b').replace('after', 'a').replace('Liquidity', 'L').replace('Remove', 'R').replace('Add', 'A').replace('Swap', 'S').replace('Donate', 'D'), (x['result'] if not x['ok'] else x['result'].replace('ok sel=', 'ok '))[:46]) for x in p.get('callbacks', [])[:8])
    print('%d %s $%-8.0f cl$%-7.0f sz%-5d %-26s pools %-6d fam %-5d [%s] init %d/%d %s %s | %s | %s' % (c['chainId'], c['hook'], c['usd'], c['claimsUsd'], c['size'], c['fl'], c['pools'], c['family'], names.get((c['chainId'], c['hook']), 'None')[:28], nok, len(init), ','.join(okv)[:60], '|'.join(errs)[:110], cbs, ' '.join('%s %s %s' % (i[0][0], i[1][:8], i[2]) for i in c['items'][:3])))
