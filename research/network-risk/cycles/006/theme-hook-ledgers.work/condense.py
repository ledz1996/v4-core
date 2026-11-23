import sys, re
from common import *
from srcscan import src, SKIPDIR
cand = json.load(open(os.path.join(RAW, 'cand.json')))
seen = {}
for c in cand:
    j = src(c['chainId'], c['hook'])
    p = {}
    for d in (RAW, os.path.join(C5, 'raw')):
        try: p = json.load(open(os.path.join(d, 'probe', '%d_%s.json' % (c['chainId'], c['hook'])))); break
        except Exception: pass
    init = p.get('init', []); nok = sum(1 for i in init if i['ok'])
    if not j:
        print('%d %s $%-7.0f sz%-5d %-22s pools %-6d NOSRC init %d/%d' % (c['chainId'], c['hook'], c['usd'], c['size'], c['fl'], c['pools'], nok, len(init))); continue
    name = (j.get('compilation') or {}).get('name')
    txt = '\n'.join(v['content'] for k, v in j['sources'].items() if not SKIPDIR.search(k) or k.split('/')[-1].split('.')[0] == name)
    txt = re.sub(r'//[^\n]*', '', txt); txt = re.sub(r'/\*.*?\*/', '', txt, flags=re.S)
    maps = re.findall(r'mapping\s*\(\s*([\w\.]+)[^;]*;', txt)
    mp = re.findall(r'(mapping\s*\([^;]*;)', txt)
    byPool = sum(1 for m in mp if re.match(r'mapping\s*\(\s*(PoolId|bytes32)', m))
    byAddr = [re.sub(r'\s+', ' ', m)[:70] for m in mp if re.match(r'mapping\s*\(\s*(address|Currency|IERC20)', m) and re.search(r'uint|int|struct|=>\s*[A-Z]', m)]
    ops = [o for o in ['burn', 'take', 'mint', 'settle', 'donate'] if re.search(r'\.%s\s*[\({]' % o, txt)]
    key = (name, len(txt))
    dup = seen.get(key); seen.setdefault(key, c['hook'][:10])
    print('%d %s $%-7.0f sz%-5d %-22s pools %-6d %-24s init %d/%d poolMaps %d addrMaps %d ops %s %s' % (c['chainId'], c['hook'], c['usd'], c['size'], c['fl'], c['pools'], name[:24], nok, len(init), byPool, len(byAddr), ','.join(ops), ('DUP of ' + dup) if dup else ' | '.join(byAddr[:6])))
