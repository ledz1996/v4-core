# Step 3 reading aid: for one representative token per code family fetch the verified source of the token, of its
# implementation and of the contracts balanceOf reads, and write out balanceOf, the transfer hooks and every function whose
# name has one of the step 3 words, with file and line numbers. The digests are read by hand.
import sys, json, os, re, glob, collections
from base import *
from fetchsrc import fetch
RX = re.compile(r'(?i)((?<![bc])lock|(?<!in)vest|cooldown|freez|frozen|escrow|idle|inactiv|sweep|reflect|claim|grant(?!Role)|revoke(?!Role)|seize|confiscat|wipe|burnFrom|forceTransfer|clawback|reclaim|recover|rescue|destroy)')
CORE = re.compile(r'^(balanceOf|_update|_transfer|_beforeTokenTransfer|_afterTokenTransfer|transfer|_spendAllowance|_burn|burn)$')
LIBS = re.compile(r'(?i)(openzeppelin|solady|solmate|forge-std|/lib/|@layerzerolabs|hardhat)')
FN = re.compile(r'\bfunction\s+([A-Za-z_0-9]+)\s*\(')
def functions(src):
    """yield (name, startline, text) for every function with a body"""
    for m in FN.finditer(src):
        i = m.start(); j = src.find('{', i); k = src.find(';', i)
        if j == -1 or (k != -1 and k < j): continue
        depth = 0; e = j
        while e < len(src):
            c = src[e]
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
            e += 1
        yield m.group(1), src.count('\n', 0, i) + 1, src[i:e + 1]
def digest(cid, addrs, label, maxlines=45):
    out = ['#### %s chain %d' % (label, cid)]
    for a in addrs:
        o = fetch(cid, a)
        out.append('## contract %s name=%s via=%s files=%d impls=%s url=%s' % (a, o['name'], o['via'], len(o['sources']), o['impls'], o['url']))
        for im in o['impls']:
            if im not in addrs: addrs.append(im)
        for path, src in o['sources'].items():
            lib = bool(LIBS.search(path))
            for nm, ln, txt in functions(src):
                if (RX.search(nm) and not lib) or (CORE.match(nm) and not lib):
                    body = txt.split('\n')
                    if len(body) > maxlines: body = body[:maxlines] + ['    ... (%d more lines)' % (len(body) - maxlines)]
                    out.append('--- %s:%d' % (path.split('/')[-1], ln))
                    out += body
    return '\n'.join(out)
if __name__ == '__main__':
    L = json.load(open(os.path.join(RAW6, 'step3_list.json')))
    disc = {}
    fams = collections.OrderedDict()
    for x in L: fams.setdefault(x['fam'], []).append(x)
    idx = []
    for k, v in fams.items():
        x = v[0]; cid = x['cid']
        if cid not in disc: disc[cid] = jz(os.path.join(RAW6, 'discover_%d.json.gz' % cid))
        o = disc[cid][x['token']]
        addrs = [x['token']] + list(o['rel'].keys())
        fn = os.path.join(RAW6, 'digest', '%s_%d_%s.txt' % (k, cid, x['token']))
        if not os.path.exists(fn):
            try: txt = digest(cid, addrs, '%s %s members=%s usd=%d' % (k, x['sym'], [y['sym'] for y in v][:8], sum(min(y['usd'], 1e12) for y in v)))
            except Exception as e: txt = 'ERR ' + str(e)
            open(fn, 'w').write(txt)
        else: txt = open(fn).read()
        nsrc = txt.count('via=sourcify') + txt.count('via=blockscout')
        idx.append((k, cid, x['token'], x['sym'], len(v), nsrc, len(txt)))
        print(k, cid, x['token'], x['sym'], len(v), 'verified contracts', nsrc, 'digest bytes', len(txt), flush=True)
    json.dump(idx, open(os.path.join(RAW6, 'digest_index.json'), 'w'))
