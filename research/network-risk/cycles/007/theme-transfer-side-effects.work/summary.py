# Per network totals of the surcharge sweep (all three passes) for the output file.
import sys, json, os, collections, glob
from base import *
def rows(cid):
    out = []
    for fn in sorted(glob.glob(os.path.join(RAW7, 'surch*_%d_div*.json.gz' % cid))):
        d = jz(fn)
        for r in d['rows']: out.append((os.path.basename(fn), d['block'], r))
    return out
def run(cid):
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    R = rows(cid); st = collections.Counter(); toks = set(); acc = set(); more = collections.defaultdict(list); pairs = set(); blocks = set()
    best = {}
    for fn, bn, r in R:
        blocks.add(bn); toks.add(r['t']); w = r['w']
        key = (r['t'], r['a'])
        if w is None: best.setdefault(key, 'callfail'); continue
        b0, r0, amt, ok, b1, r1, sk, b2 = [int(x) for x in w]
        if b0 == 0 or amt == 0: best.setdefault(key, 'zero'); continue
        if not ok: best.setdefault(key, 'refused') if best.get(key) not in ('exact', 'more', 'less') else None; continue
        loss = b0 - b1
        best[key] = 'more' if loss > amt else ('less' if loss < amt else 'exact')
        acc.add(r['t'])
        if r['kind'].split(':')[0] in ('named-pair', 'v2-pool', 'v3-pool', 'solidly-pool', 'dexscreener'): pairs.add(key)
        if loss > amt: more[r['t']].append(((loss - amt) / amt, loss - amt, r['kind'], r['a'], (r1 - r0) / amt, sk, (b2 - b1) / amt))
    c = collections.Counter(best.values())
    big = {t: v for t, v in more.items() if max(x[0] for x in v) > 1e-4 and max(x[1] for x in v) > 1000}
    small = {t: v for t, v in more.items() if t not in big}
    o = dict(chainId=cid, name=net(cid)['name'], blocks=[min(blocks), max(blocks)] if blocks else None, priced=len(live), tokensTried=len(toks), tokensWithAcceptedTransfer=len(acc), trials=len(best), accepted=c['exact'] + c['more'] + c['less'], refused=c['refused'], zero=c['zero'], callfail=c['callfail'],
             pairOrPoolRecipients=len(pairs), senderPaysMoreTokens=len(more), aboveRounding={t: dict(sym=live[t]['sym'], usd=live[t]['usd'], bal=live[t]['bal'], rows=sorted(v, reverse=True)[:6]) for t, v in big.items()},
             roundingOnly=len(small), roundingMaxUnits=max([max(x[1] for x in v) for v in small.values()] or [0]), roundingUsd=sum(live[t]['usd'] for t in small),
             roundingSyms=sorted(set((live[t]['sym'] or '?') for t in small))[:40])
    return o
if __name__ == '__main__':
    out = {}
    for cid in CIDS:
        try: o = run(cid)
        except Exception as e: print(cid, 'ERR', e); continue
        out[cid] = o
        print(cid, o['name'], 'blocks', o['blocks'], 'priced', o['priced'], 'tried', o['tokensTried'], 'tokens with an accepted transfer', o['tokensWithAcceptedTransfer'], 'trials', o['trials'], 'accepted', o['accepted'], 'refused', o['refused'], 'zero', o['zero'], 'fail', o['callfail'], 'pair recipients', o['pairOrPoolRecipients'],
              'sender pays more: tokens', o['senderPaysMoreTokens'], 'above rounding', {v['sym']: round(v['rows'][0][0] * 100, 4) for v in o['aboveRounding'].values()}, 'rounding only', o['roundingOnly'], 'max units', o['roundingMaxUnits'])
    json.dump(out, open(os.path.join(RAW7, 'surcharge_summary.json'), 'w'), indent=1)
