"""
Victim interleaving check on top of settle_model.py.
Victim V runs the canonical payment script inside its own unlock:
   V.unlock{ ; V.mint(V,c,n) [stands for any pool action that leaves V owing n and holding a claim] ;
              sync(c) ; V pays n ; V.settle() ; }
Attacker A may run up to K operations of its own in every gap (a superset of what a token callback,
a native payout recipient or a hook could do). The search reports any locked end state in which
A's wallet wealth grew, or V's wallet fell by more than n, or V ended without its claim.
"""
import sys
import settle_model as M
from collections import deque

def run(env, cname, n, K, native_pay=False):
    M.ACCTS = ('A', 'V')
    wl = {}
    for a in M.ACCTS:
        for c, v in env['wallet'].items(): wl[(a, c)] = v
    E = M.Env(env['name'], env['cur'], wl, env['pm'], env['victims'], forced=env.get('forced', False), amounts=(1,), value_amounts=(1,))
    s0 = M.S(); s0.bal = dict(E.pm); s0.wal = dict(E.wallets); s0.unlocked = False; s0.locker = None
    s0.syncC = None; s0.syncR = 0; s0.delta = {}; s0.count = 0; s0.claims = {}; s0.ops = {}
    wA0 = sum(v for (a, c), v in s0.wal.items() if a == 'A'); wV0 = sum(v for (a, c), v in s0.wal.items() if a == 'V')
    def vstep(s, i):
        """victim step i applied to state s; returns new state or None when the step reverts"""
        t = s.copy()
        if i == 0:
            if t.unlocked: return None
            t.unlocked = True; t.locker = 'V'; return t
        if i == 1:
            M.account_delta(t, cname, -n, 'V'); t.claims[('V', cname)] = t.claims.get(('V', cname), 0) + n; return t
        if i == 2:
            if E.cur[cname]['kind'] == 'native': t.syncC = None
            else: t.syncC = cname; t.syncR = M.balance_of_self(E, t, cname)
            return t
        if i == 3:
            k = E.cur[cname]
            if k['kind'] == 'native': return t          # value travels with settle
            if k['kind'] == 'erc20':
                if t.wal[('V', cname)] < n: return None
                t.wal[('V', cname)] -= n; t.bal[cname] += n; return t
            if k['kind'] == 'mirror':
                m = n * k['scale']
                if t.wal[('V', 'N')] < m: return None
                t.wal[('V', 'N')] -= m; t.bal['N'] += m; return t
        if i == 4:
            v = n if E.cur[cname]['kind'] == 'native' else 0
            if t.syncC is None:
                if E.cur[cname]['kind'] != 'native' and v == 0:
                    paid = 0; c = 'N' if 'N' in E.cur else cname
                else:
                    if t.wal[('V', 'N')] < v: return None
                    t.wal[('V', 'N')] -= v; t.bal['N'] += v; paid = v; c = 'N'
            else:
                if v > 0: return None
                c = t.syncC; now = M.balance_of_self(E, t, c)
                if now < t.syncR: return None
                paid = now - t.syncR; t.syncC = None
            M.account_delta(t, c, paid, 'V'); return t
        if i == 5:
            if t.count != 0: return None
            t.unlocked = False; t.locker = None; return t
    seen = set(); q = deque([(s0, 0, 0)]); res = {'states': 0, 'gain': 0, 'vloss': 0, 'noclaim': 0, 'completed': 0, 'ex': None}
    parent = {}
    while q:
        s, i, used = q.popleft(); res['states'] += 1
        if i == 6:
            res['completed'] += 1
            gA = sum(v for (a, c), v in s.wal.items() if a == 'A') - wA0
            lV = wV0 - sum(v for (a, c), v in s.wal.items() if a == 'V')
            scale = E.cur[cname].get('scale', 1)
            if gA > res['gain']: res['gain'] = gA; res['ex'] = (s.key(), 'gain')
            if lV > n * scale: res['vloss'] = max(res['vloss'], lV)
            if s.claims.get(('V', cname), 0) < n: res['noclaim'] += 1
            continue
        nxt = []
        t = vstep(s, i)
        if t is not None: nxt.append((t, i + 1, 0))
        if used < K:
            for lab, u in M.successors(E, s):
                if lab.startswith('V.') or lab == '}' or 'unlock{' in lab: continue
                if 'setOperator' in lab or 'xfer6909' in lab: continue
                if any(v > M.CAP_CLAIM + n for v in u.claims.values()): continue
                if any(abs(v) > M.CAP_DELTA for v in u.delta.values()): continue
                nxt.append((u, i, used + 1))
        for (u, j, k) in nxt:
            key = (u.key(), j, k)
            if key in seen: continue
            seen.add(key); q.append((u, j, k))
    return res

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    worlds = [
        (dict(name='ERC-20', cur={'N': dict(kind='native'), 'V': dict(kind='erc20')}, wallet={'N': 1, 'V': 1}, pm={'N': 2, 'V': 2}, victims={'N': 2, 'V': 2}), 'V'),
        (dict(name='native', cur={'N': dict(kind='native'), 'V': dict(kind='erc20')}, wallet={'N': 1, 'V': 1}, pm={'N': 2, 'V': 2}, victims={'N': 2, 'V': 2}), 'N'),
        (dict(name='mirror 1:1 face paid by victim', cur={'N': dict(kind='native'), 'F': dict(kind='mirror', scale=1)}, wallet={'N': 1}, pm={'N': 3}, victims={'N': 2, 'F': 1}, forced=True), 'F'),
        (dict(name='native paid by victim, mirror 1:1 face exists', cur={'N': dict(kind='native'), 'F': dict(kind='mirror', scale=1)}, wallet={'N': 1}, pm={'N': 3}, victims={'N': 2, 'F': 1}, forced=True), 'N'),
        (dict(name='scaled face paid by victim, scale 3', cur={'N': dict(kind='native'), 'F': dict(kind='mirror', scale=3)}, wallet={'N': 4}, pm={'N': 7}, victims={'N': 4, 'F': 1}, forced=False), 'F'),
    ]
    sel = int(sys.argv[2]) if len(sys.argv) > 2 else None
    for idx, (w, c) in enumerate(worlds):
        if sel is not None and idx != sel: continue
        r = run(w, c, 1, K)
        print(f"{w['name']}: K={K} states {r['states']} completed {r['completed']} attacker gain {r['gain']} victim extra loss {r['vloss']} completed without claim {r['noclaim']}", flush=True)
