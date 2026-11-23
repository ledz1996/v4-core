# Part three: for pooled tokens with rebasing indicators, find related contracts through public getters and try every
# function with at most two simple arguments on them from an ordinary account, measuring the PoolManager balance of the token.
import sys, json, gzip, os, re, collections
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import MULTI, FWD
from abi import split_types, encode, supported
from tokcode import parse
from names import SIG
from assign_sweep import item, variants, A, SINK
GET = ['stakingContract()', 'monetaryPolicy()', 'policy()', 'vault()', 'vaultAddress()', 'controller()', 'owner()', 'staking()', 'rebaser()', 'orchestrator()', 'minter()', 'manager()',
       'treasury()', 'distributor()', 'operator()', 'supplyController()', 'rebaseController()', 'exchange()', 'governance()', 'admin()', 'policyMaker()', 'oracle()', 'pool()', 'comptroller()', 'underlying()', 'asset()', 'POOL()', 'UNDERLYING_ASSET_ADDRESS()', 'getIncentivesController()', 'rewardsController()', 'stakingAddress()', 'masterChef()', 'farm()', 'strategy()', 'keeper()']
SL = ['0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', '0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3']
STRONG = {'rebase', 'gonsForBalance', 'balanceForGons', 'monetaryPolicy', 'stakingContract', 'gonsPerFragment', '_gonsPerFragment', 'rebaseOptIn', 'creditsBalanceOf', 'sharesToBalance', 'rewardMultiplier',
          'principalBalanceOf', 'scalingFactor', 'getScalingFactor', 'rebasingCreditsPerToken', 'totalFragments', 'elasticSupply', 'getRebaseFactor', 'rebaseIndex', 'inflationMultiplier', 'getInflationMultiplier', 'INDEX', 'fragmentToGons'}
def addr_of(r):
    if isinstance(r, str) and len(r) == 66:
        v = int(r, 16)
        if 2 ** 24 < v < 2 ** 160: return '0x%040x' % v
    return None
def run(cid, only=None, maxtok=400):
    toks = json.load(open(os.path.join(RAW, 'rebase_tokens.json'))).get(str(cid), {})
    toks = {t: h for t, h in toks.items() if STRONG & set(h)}
    if only: toks = {t: toks.get(t, ['manual']) for t in only}
    pm = net(cid)['poolManager']; us = urls2(cid)
    d, rows = universe(cid); bal2 = {r['token']: int(r.get('bal2') or 0) for r in rows}
    out = []; ntr = 0
    codecache = {}
    def code_sels(a):
        if a in codecache: return codecache[a]
        sels = set()
        try:
            c = rpc(us[0], 'eth_getCode', [a, 'latest'], timeout=60, tries=3)
            if len(c) > 2:
                p = parse(c); sels.update(p['sels'])
                cand = list(p.get('emb') or [])
                for s in SL:
                    v = rpc(us[0], 'eth_getStorageAt', [a, s, 'latest'], timeout=30, tries=3)
                    if int(v, 16): cand.append('0x' + v[-40:])
                for im in cand:
                    c2 = rpc(us[0], 'eth_getCode', [im, 'latest'], timeout=60, tries=3)
                    if len(c2) > 2: sels.update(parse(c2)['sels'])
        except Exception as e: pass
        codecache[a] = sels; return sels
    for t in list(toks)[:maxtok]:
        b = bal2.get(t, 0)
        r = ecall(cid, t, sel('balanceOf(address)') + adr(pm))
        if isinstance(r, str) and len(r) >= 66: b = int(r, 16)
        if b < 3: continue
        rel = {}
        for g in GET:
            a = addr_of(ecall(cid, t, sel(g), tries=3))
            if a and a != t: rel[a] = g
        for a, g in list(rel.items()):
            if g in ('monetaryPolicy()', 'policy()', 'vault()', 'vaultAddress()', 'stakingContract()', 'staking()', 'controller()'):
                for g2 in ('orchestrator()', 'distributor()', 'staking()', 'rebaser()', 'keeper()', 'strategy()'):
                    a2 = addr_of(ecall(cid, a, sel(g2), tries=2))
                    if a2 and a2 not in rel and a2 != t: rel[a2] = g + '.' + g2
        amt = max(1, b // 3)
        for a, g in rel.items():
            sels = code_sels(a)
            fns = []
            for s in sels:
                for nm in SIG.get(s) or []:
                    try: ty = split_types(nm)
                    except Exception: continue
                    if len(ty) <= 2 and supported(ty) and not nm.startswith(('transfer(', 'approve(', 'balanceOf(')): fns.append(nm); break
            items = [('BASE', adr(t) + sel('balanceOf(address)')[2:] + adr(pm))]
            for nm in sorted(set(fns)):
                for cd in variants(nm, pm, amt, int(time.time()))[:1]: items.append((nm, adr(a) + cd))
            for i in range(0, len(items), 30):
                ch = items[i:i + 30]
                if i > 0: ch = [items[0]] + ch
                data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(p) for nm, p in ch)
                r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=150_000_000)
                if not isinstance(r, str) or len(r) != 2 + 512 * len(ch): out.append(dict(token=t, rel=a, via=g, err=str(r)[:120])); continue
                ws = [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(len(ch))]
                base = ws[0]
                for (nm, p), w in zip(ch[1:], ws[1:]):
                    ntr += 1
                    if w[2] and w[3] == base[3] and w[5] == base[5] and re.search(r'(?i)^(rebase|accrue|distribut|harvest|payout|calculateInterest|stake$|unstake$|claimFor|claimOnBehalf|poke|drip|checkpoint|update)', nm):
                        out.append(dict(token=t, rel=a, via=g, callable=nm, bal=str(b), ind=toks[t]))
                    if w[2] and (w[3] != base[3] or (w[5] != base[5])):
                        out.append(dict(token=t, rel=a, via=g, fn=nm, dPM=str(w[3] - base[3]), dA=str(w[4] - base[4]), bal=str(b), full=w[5], basefull=base[5], ind=toks[t]))
    json.dump(out, open(os.path.join(RAW, 'hop_%d.json' % cid), 'w'), indent=0)
    print(cid, net(cid)['name'], 'tokens', len(toks), 'trials', ntr, 'hits', sum(1 for o in out if 'fn' in o), 'errs', sum(1 for o in out if 'err' in o), flush=True)
    cl = collections.defaultdict(list)
    for o in out:
        if 'callable' in o: cl[(o['token'], o['via'], o['rel'])].append(o['callable'].split('(')[0])
    for k, v in cl.items(): print('   callable-no-change', k, sorted(set(v))[:8], flush=True)
    for o in out:
        if 'fn' in o: print('  ', o['token'], o['via'], o['rel'], o['fn'], 'dPM', o['dPM'], 'dA', o['dA'], 'bal', o['bal'], 'full', o['full'], o['ind'][:5], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
