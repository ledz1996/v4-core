# Turn the probe files into one sentence per hook for the output file.
import json, glob, os, collections
from lib import *
from summ import census, flags
NAMES = {}
for f in glob.glob('raw/src/*.json'):
    j = json.load(open(f))
    if 'sources' in j: NAMES[os.path.basename(f)[:-5]] = j.get('compilation', {}).get('name')
SIG = json.load(open('raw/sig_lookup.json')) if os.path.exists('raw/sig_lookup.json') else {}
def errname(s):
    s = s.strip()
    if s.startswith('0x') and len(s) >= 10:
        n = SIG.get(s[2:10])
        return (n.split('(')[0] if n else 'error ' + s[:10])
    return s.split(' 0000')[0].rstrip('()').replace('(', '').replace(')', '')[:60]
def inner(res):
    r = res.split(': ', 1)[-1] if res.startswith('Wrapped(') else res
    if r.endswith(')') and res.startswith('Wrapped('): r = r[:-1]
    return errname(r)
def hook_sentence(p):
    cid = p['chainId']; h = p['hook']; nm = NAMES.get('%d_%s' % (cid, h))
    fl = ', '.join(p['flags']) or 'no flags'
    oks = [i for i in p['init'] if i['ok']]; bad = [i for i in p['init'] if not i['ok']]
    if not oks:
        rs = collections.Counter(inner(i['result']) for i in bad)
        init = 'initialize by an ordinary account reverts in all %d PoolKey variants (%s)' % (len(bad), ', '.join(rs))
    elif not bad:
        init = 'initialize by an ordinary account succeeds in all %d PoolKey variants' % len(oks)
    else:
        rs = collections.Counter(inner(i['result']) for i in bad)
        def lab(v):
            if v.startswith('own pair'): return 'the currency pair of an existing pool with another tick spacing'
            b = v.split(' fee')[0].split(' ts')[0].split(' dynamic')[0]
            if b.startswith('foreign real pair'): b = 'a real pair that the hook does not serve'
            return b + (' with the dynamic fee flag' if 'dynamic' in v else '')
        init = 'initialize by an ordinary account succeeds for %s and reverts for the other variants (%s)' % ('; '.join(sorted(set(lab(i['variant']) for i in oks))), ', '.join(rs))
    k0 = p['callbacks'][0]['key'] if p['callbacks'] else None
    cbs = []
    for c in p['callbacks']:
        if c['key'] != k0: continue
        if c['ok']:
            r = c['result']; d = ''
            if 'ret1=' in r:
                t = r.split('ret1=')[1]; a = t.split(' ret2=')[0].strip(); b = t.split('ret2=')[1].strip() if 'ret2=' in t else ''
                if a: d = ' with a non zero delta'
                elif b: d = ' with fee override 0x' + b
            cbs.append('%s returns%s' % (c['fn'], d or (' with zero delta' if ('Swap' in c['fn'] or 'after' in c['fn']) else '')))
        else:
            cbs.append('%s reverts (%s)' % (c['fn'], errname(c['result'])))
    cb = '; '.join(cbs)
    hold = ''
    hf = 'raw/probe/hold_%d_%s.json' % (cid, h)
    if os.path.exists(hf):
        o = json.load(open(hf)); cl = sum(1 for e in o['cur'].values() if isinstance(e.get('claims'), int) and e['claims'] > 0); er = sum(1 for e in o['cur'].values() if isinstance(e.get('erc20'), int) and e['erc20'] > 0)
        nat = o.get('native') or 0
        if cid == 4217: nat = 0
        parts = []
        if cl: parts.append('ERC-6909 claims in %d' % cl)
        if er: parts.append('token balances in %d' % er)
        hold = ''
        if parts: hold = ' It holds ' + ' and '.join(parts) + ' of the %d pool currencies checked%s.' % (len(o['cur']), ', and a native balance' if nat else '')
        elif nat: hold = ' It holds a native balance and nothing in the %d pool currencies checked.' % len(o['cur'])
        else: hold = ' It holds no claims, token balances or native balance in the %d pool currencies checked.' % len(o['cur'])
    proxy = p.get('proxy1167') or p.get('impl1967')
    return '%s%s (%d pool%s, %d bytes%s; flags %s): %s. Callbacks called from the PoolManager address with a PoolKey the hook did not create: %s.%s' % (h, ' ' + nm if nm else ', source not verified', p['pools'], '' if p['pools'] == 1 else 's', p['codeLen'], ', proxy to ' + proxy if proxy else '', fl, init, cb or 'no callback besides initialize', hold)
def chain_block(cid, N=5, extra=()):
    cnt, dyn, rows, total, cov = census(cid)
    z = '0x' + '0' * 40
    top = [h for h, _ in sorted(((h, c) for h, c in cnt.items() if h != z), key=lambda x: -x[1])[:N]]
    for h in extra:
        if h not in top: top.append(h)
    out = []
    for h in top:
        f = 'raw/probe/%d_%s.json' % (cid, h)
        if os.path.exists(f):
            p = json.load(open(f)); p['pools'] = cnt.get(h, p['pools']); out.append(hook_sentence(p))
        else: out.append('%s (%d pools): not probed.' % (h, cnt.get(h, 0)))
    return dict(total=total, withHook=total - cnt.get(z, 0), distinct=len(cnt) - (1 if z in cnt else 0), cov=cov, hooks=out, top=top)
if __name__ == '__main__':
    import sys
    b = chain_block(int(sys.argv[1]))
    print(b['total'], b['withHook'], b['distinct'], b['cov'])
    for x in b['hooks']: print(' -', x)
