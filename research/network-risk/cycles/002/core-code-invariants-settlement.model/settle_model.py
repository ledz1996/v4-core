"""
Model of the settlement layer of src/PoolManager.sol (lines 104-114, 279-378),
src/libraries/CurrencyDelta.sol, CurrencyReserves.sol, NonzeroDeltaCount.sol, Lock.sol,
src/types/Currency.sol (transfer / balanceOfSelf) and src/ERC6909.sol / ERC6909Claims.sol.

Exhaustive search over operation sequences by two colluding accounts A and B.
Everything in one sequence is one transaction (superset of "several unlocks in a bundle"),
so a stale sync survives between unlocks. A sequence may only "end" when the manager is locked.

Checked at every locked state:
  GAIN     : combined wallet wealth of A and B, counted in base units of the real assets, exceeds the start
  SOLVENCY : real PoolManager balance of an asset < obligations to victims + ERC-6909 claims that can be paid out
"""
import sys, itertools
from collections import deque

INT128_MAX = (1 << 127) - 1
ACCTS = ('A', 'B')
CAP_CLAIM = 2
CAP_DELTA = 4

class Env:
    """currencies: name -> dict(kind=..., asset=..., scale=...)
       kinds: native | erc20 | mirror (balanceOf = floor(native/scale), transfer moves n*scale native)
              mirror_notransfer (balanceOf mirrors, transfer reverts for n>0)
              ledger (balanceOf = deposit ledger raised by native sends from the PoolManager, no transfer)
              wrapper (ERC-20 minted 1:1 to sender of native; transfer works)
    """
    def __init__(self, name, currencies, wallets, pm, victims, forced=False, amounts=(1, 2), value_amounts=(1, 2)):
        import os
        if os.environ.get('AMT1'): amounts = (1,); value_amounts = (1,)
        self.name = name; self.cur = currencies; self.wallets = wallets; self.pm = pm
        self.victims = victims; self.forced = forced; self.amounts = amounts; self.value_amounts = value_amounts

def freeze(d):
    return tuple(sorted(d.items()))

class S:
    __slots__ = ('bal', 'wal', 'unlocked', 'locker', 'syncC', 'syncR', 'delta', 'count', 'claims', 'ops')
    def __init__(self):
        pass
    def key(self):
        return (freeze(self.bal), freeze(self.wal), self.unlocked, self.locker, self.syncC, self.syncR,
                tuple(sorted((k, v) for k, v in self.delta.items() if v != 0)), self.count,
                tuple(sorted((k, v) for k, v in self.claims.items() if v != 0)), freeze(self.ops))
    def copy(self):
        n = S(); n.bal = dict(self.bal); n.wal = dict(self.wal); n.unlocked = self.unlocked; n.locker = self.locker
        n.syncC = self.syncC; n.syncR = self.syncR; n.delta = dict(self.delta); n.count = self.count
        n.claims = dict(self.claims); n.ops = dict(self.ops); return n

def balance_of_self(env, s, c):
    """Currency.balanceOfSelf for a non native currency (Currency.sol:90-96) as the token answers it."""
    k = env.cur[c]
    if k['kind'] == 'erc20' or k['kind'] == 'wrapper' or k['kind'] == 'ledger':
        return s.bal[c]
    if k['kind'] in ('mirror', 'mirror_notransfer'):
        return s.bal['N'] // k['scale']
    raise Exception(k)

def account_delta(s, c, d, target):
    """PoolManager._accountDelta (PoolManager.sol:368-378) and CurrencyDelta.applyDelta."""
    if d == 0:
        return
    prev = s.delta.get((target, c), 0)
    nxt = prev + d
    s.delta[(target, c)] = nxt
    if nxt == 0:
        s.count -= 1
    elif prev == 0:
        s.count += 1

def pay_out(env, s, c, to, n):
    """Currency.transfer (Currency.sol:40-88). Returns False on revert."""
    k = env.cur[c]
    if k['kind'] == 'native':
        if s.bal['N'] < n: return False
        s.bal['N'] -= n
        if to in ACCTS:
            s.wal[(to, 'N')] += n
        elif to == 'PM':
            return False            # no receive or fallback in the PoolManager
        else:                       # to is a contract currency address: wrapper or ledger credit the sender
            kk = env.cur[to]
            if kk['kind'] in ('wrapper', 'ledger'):
                s.bal[to] += n      # msg.sender is the PoolManager
            else:
                return False
        return True
    if k['kind'] in ('erc20', 'wrapper'):
        if s.bal[c] < n: return False
        if to == 'PM': return True  # self transfer
        if to not in ACCTS: return False
        s.bal[c] -= n; s.wal[(to, c)] += n; return True
    if k['kind'] == 'mirror':
        m = n * k['scale']
        if s.bal['N'] < m: return False
        if to == 'PM': return True
        if to not in ACCTS: return False
        s.bal['N'] -= m; s.wal[(to, 'N')] += m; return True
    if k['kind'] in ('mirror_notransfer', 'ledger'):
        return n == 0 and k['kind'] == 'mirror_notransfer'
    raise Exception(k)

def wealth(env, s):
    return sum(v for (a, c), v in s.wal.items())

def successors(env, s):
    out = []
    curs = list(env.cur.keys())
    def push(label, n):
        out.append((label, n))
    # unlock / close
    if not s.unlocked:
        for a in ACCTS:
            n = s.copy(); n.unlocked = True; n.locker = a; push(f'{a}.unlock{{', n)
    else:
        if s.count == 0:
            n = s.copy(); n.unlocked = False; n.locker = None; push('}', n)
    # sync: no lock check (PoolManager.sol:279-288)
    for c in curs:
        n = s.copy()
        if env.cur[c]['kind'] == 'native':
            n.syncC = None
        else:
            n.syncC = c; n.syncR = balance_of_self(env, s, c)
        if (n.syncC, n.syncR) != (s.syncC, s.syncR):
            push(f'sync({c})', n)
    # direct payments into the PoolManager by wallet holders (token transfer, mirror transfer, forced native)
    for a in ACCTS:
        for c in curs:
            k = env.cur[c]
            for amt in env.amounts:
                if k['kind'] in ('erc20', 'wrapper'):
                    if s.wal[(a, c)] >= amt:
                        n = s.copy(); n.wal[(a, c)] -= amt; n.bal[c] += amt; push(f'{a}.send({c},{amt})', n)
                elif k['kind'] == 'mirror':
                    m = amt * k['scale']
                    if s.wal[(a, 'N')] >= m:
                        n = s.copy(); n.wal[(a, 'N')] -= m; n.bal['N'] += m; push(f'{a}.faceSend({c},{amt})', n)
                elif k['kind'] == 'native' and env.forced:
                    if s.wal[(a, 'N')] >= amt:
                        n = s.copy(); n.wal[(a, 'N')] -= amt; n.bal['N'] += amt; push(f'{a}.force(N,{amt})', n)
    # ERC-6909 outside or inside the lock (ERC6909.sol:25-64)
    for a in ACCTS:
        b = 'B' if a == 'A' else 'A'
        if b not in ACCTS: continue
        for c in curs:
            v = s.claims.get((a, c), 0)
            for amt in env.amounts:
                if v >= amt:
                    n = s.copy(); n.claims[(a, c)] = v - amt; n.claims[(b, c)] = n.claims.get((b, c), 0) + amt
                    push(f'{a}.xfer6909({c},{amt})', n)
        if not s.ops.get((a, b), False):
            n = s.copy(); n.ops[(a, b)] = True; push(f'{a}.setOperator({b})', n)
    if s.unlocked:
        for a in ACCTS:
            b = 'B' if a == 'A' else 'A'
            # settle / settleFor (PoolManager.sol:300-307, 349-365)
            for rcpt in ACCTS:
                vals = (0,) + tuple(env.value_amounts)
                for v in vals:
                    if 'N' in env.cur and s.wal.get((a, 'N'), 0) < v: continue
                    if v > 0 and 'N' not in env.cur: continue
                    n = s.copy()
                    if n.syncC is None:
                        paid = v
                        if v > 0:
                            n.wal[(a, 'N')] -= v; n.bal['N'] += v
                        c = 'N' if 'N' in env.cur else None
                        if c is None:
                            if paid: continue
                            continue
                    else:
                        if v > 0: continue          # NonzeroNativeValue
                        c = n.syncC
                        now = balance_of_self(env, n, c)
                        if now < n.syncR: continue  # checked subtraction
                        paid = now - n.syncR
                        n.syncC = None
                    if paid == 0 and n.syncC == s.syncC: continue
                    account_delta(n, c, paid, rcpt)
                    push(f'{a}.settleFor({rcpt},value={v})', n)
            for c in curs:
                # take (PoolManager.sol:291-297)
                tos = list(ACCTS) + [x for x in curs if env.cur[x]['kind'] in ('wrapper', 'ledger')] + ['PM']
                for to in tos:
                    for amt in (0,) + tuple(env.amounts):
                        n = s.copy()
                        account_delta(n, c, -amt, a)
                        if not pay_out(env, n, c, to, amt): continue
                        if n.key() == s.key(): continue
                        push(f'{a}.take({c},{to},{amt})', n)
                for amt in env.amounts:
                    # mint (PoolManager.sol:322-329)
                    for to in ACCTS:
                        n = s.copy(); account_delta(n, c, -amt, a); n.claims[(to, c)] = n.claims.get((to, c), 0) + amt
                        push(f'{a}.mint({to},{c},{amt})', n)
                    # burn (PoolManager.sol:332-336, ERC6909Claims.sol:13-22); allowance path left out, operator path kept
                    for frm in ACCTS:
                        if frm != a and not s.ops.get((frm, a), False): continue
                        if s.claims.get((frm, c), 0) < amt: continue
                        n = s.copy(); account_delta(n, c, amt, a); n.claims[(frm, c)] -= amt
                        push(f'{a}.burn({frm},{c},{amt})', n)
                # clear (PoolManager.sol:310-319)
                cur = s.delta.get((a, c), 0)
                if cur > 0:
                    n = s.copy(); account_delta(n, c, -cur, a); push(f'{a}.clear({c},{cur})', n)
    return out

def obligations_ok(env, s):
    """real balance of each asset must cover victim obligations plus payable ERC-6909 claims"""
    need = {}
    for c, k in env.cur.items():
        v = env.victims.get(c, 0)
        cl = sum(val for (a, cc), val in s.claims.items() if cc == c)
        if k['kind'] == 'native':
            need['N'] = need.get('N', 0) + v + cl
        elif k['kind'] in ('erc20', 'wrapper'):
            need[c] = need.get(c, 0) + v + cl
        elif k['kind'] == 'mirror':
            need['N'] = need.get('N', 0) + (v + cl) * k['scale']
        # mirror_notransfer and ledger claims can never be paid out; they are not obligations on the asset
    bad = []
    for asset, n in need.items():
        if s.bal[asset] < n:
            bad.append((asset, s.bal[asset], n))
    return bad

def run(env, depth):
    s0 = S()
    s0.bal = dict(env.pm); s0.wal = dict(env.wallets); s0.unlocked = False; s0.locker = None
    s0.syncC = None; s0.syncR = 0; s0.delta = {}; s0.count = 0; s0.claims = {}; s0.ops = {}
    w0 = wealth(env, s0)
    seen = {s0.key(): None}
    q = deque([(s0, 0)])
    best_gain = 0; best_path = None; insolv = None; states = 0; maxcount = 0
    parent = {s0.key(): (None, None)}
    def path(k):
        p = []
        while parent[k][0] is not None:
            k, lab = parent[k]; p.append(lab)
        return list(reversed(p))
    while q:
        s, d = q.popleft(); states += 1
        if not s.unlocked:
            g = wealth(env, s) - w0
            if g > best_gain:
                best_gain = g; best_path = path(s.key())
            bad = obligations_ok(env, s)
            if bad and insolv is None:
                insolv = (bad, path(s.key()))
            # delta sum check: every delta slot is zero when locked
            assert all(v == 0 for v in s.delta.values()) and s.count == 0
        if depth and d == depth: continue
        for lab, n in successors(env, s):
            if n.count < 0: raise Exception('count underflow ' + str(path(s.key()) + [lab]))
            if n.count != sum(1 for v in n.delta.values() if v != 0): raise Exception('count mismatch ' + str(path(s.key()) + [lab]))
            if any(v > CAP_CLAIM for v in n.claims.values()): continue
            if any(abs(v) > CAP_DELTA for v in n.delta.values()): continue
            k = n.key()
            if k in parent: continue
            parent[k] = (s.key(), lab)
            q.append((n, d + 1))
    return states, best_gain, best_path, insolv

if __name__ == '__main__':
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    which = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if len(sys.argv) > 3:
        ACCTS = tuple(sys.argv[3])
    if len(sys.argv) > 4: CAP_CLAIM = int(sys.argv[4])
    if len(sys.argv) > 5: CAP_DELTA = int(sys.argv[5])
    def wl(d):
        out = {}
        for a in ACCTS:
            for c, v in d.items(): out[(a, c)] = v
        return out
    envs = []
    envs.append(Env('plain: native + ERC-20', {'N': dict(kind='native'), 'V': dict(kind='erc20')},
                    wl({'N': 2, 'V': 2}), {'N': 5, 'V': 5}, {'N': 5, 'V': 5}))
    envs.append(Env('mirror 1:1 with transfer (CELO token shape)', {'N': dict(kind='native'), 'F': dict(kind='mirror', scale=1)},
                    wl({'N': 3}), {'N': 6}, {'N': 3, 'F': 3}, forced=True))
    envs.append(Env('mirror 1:1 without transfer (0x1010 / LegacyERC20ETH shape)', {'N': dict(kind='native'), 'F': dict(kind='mirror_notransfer', scale=1)},
                    wl({'N': 3}), {'N': 6}, {'N': 6}, forced=True))
    envs.append(Env('scaled mirror, scale 3, forced native sends allowed (Arc 0x3600 shape)', {'N': dict(kind='native'), 'F': dict(kind='mirror', scale=3)},
                    wl({'N': 7}), {'N': 13}, {'N': 4, 'F': 3}, forced=True, amounts=(1, 2), value_amounts=(1, 2)))
    envs.append(Env('scaled mirror, scale 3, no forced native sends', {'N': dict(kind='native'), 'F': dict(kind='mirror', scale=3)},
                    wl({'N': 7}), {'N': 13}, {'N': 4, 'F': 3}, forced=False))
    envs.append(Env('wrapper credited to sender (WETH9 shape)', {'N': dict(kind='native'), 'W': dict(kind='wrapper')},
                    wl({'N': 2, 'W': 2}), {'N': 5, 'W': 5}, {'N': 5, 'W': 5}))
    envs.append(Env('deposit ledger without transfer (EntryPoint shape)', {'N': dict(kind='native'), 'E': dict(kind='ledger')},
                    wl({'N': 3}), {'N': 5, 'E': 0}, {'N': 5}))
    import os
    if os.environ.get('SMALL'):
        envs = []
        envs.append(Env('plain small', {'N': dict(kind='native'), 'V': dict(kind='erc20')}, wl({'N': 1, 'V': 1}), {'N': 2, 'V': 2}, {'N': 2, 'V': 2}))
        envs.append(Env('mirror 1:1 with transfer small', {'N': dict(kind='native'), 'F': dict(kind='mirror', scale=1)}, wl({'N': 1}), {'N': 3}, {'N': 2, 'F': 1}, forced=True))
        envs.append(Env('ERC-20 only small', {'V': dict(kind='erc20')}, wl({'V': 1}), {'V': 2}, {'V': 2}))
        envs.append(Env('native only small', {'N': dict(kind='native')}, wl({'N': 1}), {'N': 2}, {'N': 2}))
    for i, env in enumerate(envs):
        if which != 'all' and str(i) != which: continue
        states, gain, p, insolv = run(env, depth)
        print(f'[{i}] {env.name}: accounts {ACCTS}, depth {depth or "exhaustive"}, caps claim {CAP_CLAIM} delta {CAP_DELTA}, states {states}, best gain {gain}', flush=True)
        if p: print('     gain path:', ' ; '.join(p))
        if insolv: print('     INSOLVENT:', insolv[0], ' ; '.join(insolv[1]))
