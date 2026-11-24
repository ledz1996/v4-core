"""Shows the comparison can fail: recompute principal with the opposite rounding and fees with one unit more,
and count how many checked single-action transactions would then disagree with what was paid."""
import json, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
for f in sys.argv[1:]:
    d = json.load(open(f)); R = [r for r in d['results'] if r.get('kind') in ('remove',) and 'result' in r]
    flip = 0; tested = 0
    for r in R:
        e = r['detail'][0]; L = -int(e['delta'])
        # needs the price: take it from principal consistency only when one side is zero; otherwise count by recomputing via ticks
        pl, pu = m.get_sqrt_price_at_tick(e['tl']), m.get_sqrt_price_at_tick(e['tu'])
        p0, p1 = int(e['principal'][0]), int(e['principal'][1])
        if p1 == 0: alt0, alt1 = m.amount0_delta(pl, pu, L, True), 0
        elif p0 == 0: alt0, alt1 = 0, m.amount1_delta(pl, pu, L, True)
        else: continue
        tested += 1
        if (alt0, alt1) != (p0, p1): flip += 1
    C = [r for r in d['results'] if 'result' in r and any(int(x) for e in r['detail'] if 'fees' in e for x in e['fees'])]
    print(d['chainId'], 'out-of-range removals', tested, 'where round-up principal would differ from what was paid', flip, '; transactions with fees, all of which a +1 unit fee would break:', len(C))
