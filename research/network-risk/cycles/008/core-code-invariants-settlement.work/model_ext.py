"""
Extended state model of the settlement layer, cycle 8.
Source lines modelled: src/PoolManager.sol:104-114 (unlock), 279-288 (sync), 291-297 (take),
300-307 and 349-365 (settle, settleFor, _settle), 310-319 (clear), 322-336 (mint, burn),
368-378 (_accountDelta); src/libraries/CurrencyReserves.sol:21-32; src/types/Currency.sol:40-96;
src/ERC6909.sol:25-64; src/ERC6909Claims.sol:13-22.

New against cycles/002/core-code-invariants-settlement.model/settle_model.py:
  * a currency is (asset ledger, view num/den, payout rule), so several currency ids can sit on one
    ledger at once (three ids on Celo, two ERC-20 ids on one token ledger, a rate face over a share ledger)
  * a wrapper that mints to the sender of native value can coexist with a face of the native balance
  * wallets can wrap and unwrap
Everything in one sequence is one transaction. A sequence may only end while the manager is locked.
"""
import sys
from collections import deque

class Cur:
    def __init__(self, kind, asset=None, num=1, den=1, pays=True):
        self.kind = kind; self.asset = asset; self.num = num; self.den = den; self.pays = pays

class Env:
    def __init__(self, name, cur, wallets, pm, victims, forced=False, amounts=(1, 2), accts=('A',),
                 cap_claim=2, cap_delta=4):
        self.name = name; self.cur = cur; self.wallets = wallets; self.pm = pm; self.victims = victims
        self.forced = forced; self.amounts = amounts; self.accts = accts
        self.cap_claim = cap_claim; self.cap_delta = cap_delta

def fz(d): return tuple(sorted((k, v) for k, v in d.items() if v))

class S:
    __slots__ = ('bal', 'wal', 'unlocked', 'syncC', 'syncR', 'delta', 'count', 'claims', 'ops', 'lost')
    def key(self):
        return (fz(self.bal), fz(self.wal), self.unlocked, self.syncC, self.syncR if self.syncC else 0,
                fz(self.delta), self.count, fz(self.claims), fz(self.ops))
    def copy(self):
        n = S(); n.bal = dict(self.bal); n.wal = dict(self.wal); n.unlocked = self.unlocked
        n.syncC = self.syncC; n.syncR = self.syncR; n.delta = dict(self.delta); n.count = self.count
        n.claims = dict(self.claims); n.ops = dict(self.ops); n.lost = self.lost; return n

def bal_of(env, s, c):
    k = env.cur[c]
    if k.kind == 'erc20' or k.kind == 'wrapper': return s.bal.get(c, 0)
    if k.kind == 'face': return s.bal.get(k.asset, 0) * k.num // k.den
    raise Exception(c)

def acct(s, c, d, target):
    if d == 0: return
    prev = s.delta.get((target, c), 0); nxt = prev + d
    s.delta[(target, c)] = nxt
    if nxt == 0: s.count -= 1
    elif prev == 0: s.count += 1

def face_units(k, n):
    """asset units that a face transfer of n face units moves"""
    if k.num == 1: return n * k.den            # integer scale, exact
    return n * k.den // k.num                  # rate face: shares rounded down (stETH style)

def pay_out(env, s, c, to, n):
    k = env.cur[c]
    if k.kind == 'native':
        if s.bal.get('N', 0) < n: return False
        if to == 'PM': return False                       # no receive, no fallback
        if to in env.accts:
            s.bal['N'] -= n; s.wal[(to, 'N')] = s.wal.get((to, 'N'), 0) + n; return True
        kk = env.cur[to]
        if kk.kind == 'wrapper':                           # receive() mints to msg.sender, the PoolManager
            s.bal['N'] -= n; s.bal[to] = s.bal.get(to, 0) + n; return True
        return False                                       # a face contract has no payable receive
    if k.kind in ('erc20', 'wrapper'):
        if s.bal.get(c, 0) < n: return False
        if to == 'PM': return True
        if to not in env.accts: return n == 0
        s.bal[c] -= n; s.wal[(to, c)] = s.wal.get((to, c), 0) + n; return True
    if k.kind == 'face':
        if not k.pays: return n == 0
        m = face_units(k, n)
        if s.bal.get(k.asset, 0) < m: return False
        if to == 'PM': return True
        if to in env.accts:
            s.bal[k.asset] -= m; s.wal[(to, k.asset)] = s.wal.get((to, k.asset), 0) + m; return True
        kk = env.cur[to]
        if kk.kind == 'wrapper' and k.asset == 'N':        # moves native into the wrapper without a call: no mint
            s.bal['N'] -= m; s.lost += m; return True
        return n == 0
    raise Exception(c)

def wealth(env, s):
    return sum(v for v in s.wal.values())

def successors(env, s):
    out = []
    curs = list(env.cur.keys())
    A = env.accts
    if not s.unlocked:
        n = s.copy(); n.unlocked = True; out.append(('unlock{', n))
    elif s.count == 0:
        n = s.copy(); n.unlocked = False; out.append(('}', n))
    for c in curs:                                         # sync, no lock check
        n = s.copy()
        if env.cur[c].kind == 'native': n.syncC = None; n.syncR = 0
        else: n.syncC = c; n.syncR = bal_of(env, s, c)
        if (n.syncC, n.syncR) != (s.syncC, s.syncR if s.syncC else 0): out.append((f'sync({c})', n))
    assets = set(['N'] if 'N' in env.cur else [])
    for c, k in env.cur.items():
        if k.kind in ('erc20', 'wrapper'): assets.add(c)
    for a in A:
        for asset in assets:                               # direct payments into the PoolManager
            for amt in env.amounts:
                if s.wal.get((a, asset), 0) < amt: continue
                if asset == 'N':
                    ok = env.forced
                    if not ok:                             # only through a paying 1:n face of the native balance
                        ok = any(k.kind == 'face' and k.asset == 'N' and k.pays and k.num == 1 and amt % k.den == 0
                                 for k in env.cur.values())
                    if not ok: continue
                n = s.copy(); n.wal[(a, asset)] -= amt; n.bal[asset] = n.bal.get(asset, 0) + amt
                out.append((f'{a}.send({asset},{amt})', n))
        for c, k in env.cur.items():                       # wrap and unwrap in the wallet
            if k.kind != 'wrapper': continue
            for amt in env.amounts:
                if s.wal.get((a, 'N'), 0) >= amt:
                    n = s.copy(); n.wal[(a, 'N')] -= amt; n.wal[(a, c)] = n.wal.get((a, c), 0) + amt
                    out.append((f'{a}.wrap({amt})', n))
                if s.wal.get((a, c), 0) >= amt:
                    n = s.copy(); n.wal[(a, c)] -= amt; n.wal[(a, 'N')] = n.wal.get((a, 'N'), 0) + amt
                    out.append((f'{a}.unwrap({amt})', n))
        for b in A:                                        # ERC-6909 transfers and operators
            if b == a: continue
            for c in curs:
                v = s.claims.get((a, c), 0)
                for amt in env.amounts:
                    if v >= amt:
                        n = s.copy(); n.claims[(a, c)] = v - amt; n.claims[(b, c)] = n.claims.get((b, c), 0) + amt
                        out.append((f'{a}.xfer6909({c},{amt})', n))
            if not s.ops.get((a, b)):
                n = s.copy(); n.ops[(a, b)] = 1; out.append((f'{a}.setOperator({b})', n))
    if s.unlocked:
        for a in A:
            for rcpt in A:
                for v in (0,) + tuple(env.amounts):
                    if v and ('N' not in env.cur or s.wal.get((a, 'N'), 0) < v): continue
                    n = s.copy()
                    if n.syncC is None:
                        if 'N' not in env.cur: continue
                        if v == 0: continue
                        n.wal[(a, 'N')] -= v; n.bal['N'] = n.bal.get('N', 0) + v
                        acct(n, 'N', v, rcpt)
                    else:
                        if v: continue                     # NonzeroNativeValue
                        c = n.syncC; now = bal_of(env, n, c)
                        if now < n.syncR: continue         # checked subtraction
                        paid = now - n.syncR; n.syncC = None; n.syncR = 0
                        acct(n, c, paid, rcpt)
                    out.append((f'{a}.settleFor({rcpt},value={v})', n))
            for c in curs:
                tos = list(A) + [x for x in curs if env.cur[x].kind == 'wrapper'] + ['PM']
                for to in tos:
                    for amt in (0,) + tuple(env.amounts):
                        n = s.copy(); acct(n, c, -amt, a)
                        if not pay_out(env, n, c, to, amt): continue
                        if n.key() == s.key(): continue
                        out.append((f'{a}.take({c},{to},{amt})', n))
                for amt in env.amounts:
                    for to in A:
                        n = s.copy(); acct(n, c, -amt, a); n.claims[(to, c)] = n.claims.get((to, c), 0) + amt
                        out.append((f'{a}.mint({to},{c},{amt})', n))
                    for frm in A:
                        if frm != a and not s.ops.get((frm, a)): continue
                        if s.claims.get((frm, c), 0) < amt: continue
                        n = s.copy(); acct(n, c, amt, a); n.claims[(frm, c)] -= amt
                        out.append((f'{a}.burn({frm},{c},{amt})', n))
                cur = s.delta.get((a, c), 0)
                if cur > 0:
                    n = s.copy(); acct(n, c, -cur, a); out.append((f'{a}.clear({c},{cur})', n))
    return out

def shortfall(env, s):
    need = {}
    for c, k in env.cur.items():
        units = env.victims.get(c, 0) + sum(v for (a, cc), v in s.claims.items() if cc == c)
        if k.kind == 'native': need['N'] = need.get('N', 0) + units
        elif k.kind in ('erc20', 'wrapper'): need[c] = need.get(c, 0) + units
        elif k.kind == 'face' and k.pays: need[k.asset] = need.get(k.asset, 0) + face_units(k, units)
    return [(a, s.bal.get(a, 0), n) for a, n in need.items() if s.bal.get(a, 0) < n]

def run(env, limit=0):
    s0 = S(); s0.bal = dict(env.pm); s0.wal = dict(env.wallets); s0.unlocked = False; s0.syncC = None; s0.syncR = 0
    s0.delta = {}; s0.count = 0; s0.claims = {}; s0.ops = {}; s0.lost = 0
    w0 = wealth(env, s0)
    parent = {s0.key(): (None, None)}
    q = deque([s0]); states = 0; best = 0; bestp = None; ins = None
    def path(k):
        p = []
        while parent[k][0] is not None:
            k, lab = parent[k]; p.append(lab)
        return list(reversed(p))
    while q:
        s = q.popleft(); states += 1
        if limit and states >= limit: return states, best, bestp, ins, True
        if not s.unlocked:
            assert s.count == 0 and not any(s.delta.values())
            g = wealth(env, s) - w0
            if g > best: best = g; bestp = path(s.key())
            bad = shortfall(env, s)
            if bad and ins is None: ins = (bad, path(s.key()))
        for lab, n in successors(env, s):
            assert n.count == sum(1 for v in n.delta.values() if v), lab
            if any(v > env.cap_claim for v in n.claims.values()): continue
            if any(abs(v) > env.cap_delta for v in n.delta.values()): continue
            k = n.key()
            if k in parent: continue
            parent[k] = (s.key(), lab); q.append(n)
    return states, best, bestp, ins, False

def wl(accts, d):
    return {(a, c): v for a in accts for c, v in d.items()}

def envs():
    E = []
    A1 = ('A',)
    # 0: Celo shape with three ids on the native balance: address(0), the CELO token face, the wrapped native predeploy
    E.append(Env('Celo triple: native + 1:1 face with transfer + wrapper, forced sends',
                 {'N': Cur('native'), 'F': Cur('face', 'N'), 'W': Cur('wrapper')},
                 wl(A1, {'N': 1}), {'N': 4, 'W': 1}, {'N': 2, 'F': 2, 'W': 1}, forced=True, amounts=(1,), cap_claim=1, cap_delta=2))
    # 1: two ERC-20 ids over one token ledger (double entry token, Monerium EURe shape)
    E.append(Env('two ERC-20 ids on one token ledger, both pay',
                 {'T': Cur('erc20'), 'T2': Cur('face', 'T')},
                 wl(A1, {'T': 2}), {'T': 6}, {'T': 3, 'T2': 3}))
    # 2: Arc shape with a second face that reports the same scaled figure and cannot pay (implementation address)
    E.append(Env('Arc double face: native + scaled face that pays + scaled face that does not pay, no forced sends',
                 {'N': Cur('native'), 'F': Cur('face', 'N', 1, 3), 'G': Cur('face', 'N', 1, 3, pays=False)},
                 wl(A1, {'N': 7}), {'N': 13}, {'N': 4, 'F': 3}, forced=False))
    # 3: rate face over a share ledger where the share token is itself a currency (stHYPE over wstHYPE shape), rate 3/2
    E.append(Env('rate face 3/2 over a share token that is also a currency',
                 {'S': Cur('erc20'), 'R': Cur('face', 'S', 3, 2)},
                 wl(A1, {'S': 4}), {'S': 8}, {'S': 4, 'R': 6}, amounts=(1, 2, 3)))
    # 4: coarse ERC-20 face over a fine ERC-20 ledger: 1 face unit = 3 ledger units, both transferable
    E.append(Env('coarse ERC-20 face (1 unit = 3 ledger units) over a fine ERC-20 ledger, both pay',
                 {'S': Cur('erc20'), 'C': Cur('face', 'S', 1, 3)},
                 wl(A1, {'S': 7}), {'S': 13}, {'S': 4, 'C': 3}))
    # 5: Celo triple with two cooperating accounts, amount 1 only
    A2 = ('A', 'B')
    E.append(Env('Celo triple, two accounts, amounts of 1',
                 {'N': Cur('native'), 'F': Cur('face', 'N'), 'W': Cur('wrapper')},
                 wl(A2, {'N': 1}), {'N': 4, 'W': 1}, {'N': 2, 'F': 2, 'W': 1}, forced=True, amounts=(1,), accts=A2,
                 cap_claim=1, cap_delta=2))
    return E

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for i, env in enumerate(envs()):
        if which != 'all' and str(i) != which: continue
        states, gain, p, ins, cut = run(env, int(sys.argv[2]) if len(sys.argv) > 2 else 0)
        print(f'[{i}] {env.name}: accounts {env.accts}, amounts {env.amounts}, caps claim {env.cap_claim} delta {env.cap_delta}, states {states}{' (stopped at the limit, not exhaustive)' if cut else ' (exhaustive)'}, best gain {gain}', flush=True)
        if p: print('     gain path:', ' ; '.join(p))
        if ins: print('     SHORTFALL:', ins[0], ' ; '.join(ins[1]))
