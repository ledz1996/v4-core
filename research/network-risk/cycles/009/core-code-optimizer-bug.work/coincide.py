"""Calls of the built PoolManager in which two storage locations that the source computes separately coincide at run time,
run in the reference interpreter (tools/opdiff/pyevm.py). Expected values come from the text of src/ERC6909.sol:25-62."""
import sys, json, os, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
os.environ.setdefault('PM_BUILD', '/home/user/v4-core/research/network-risk/build/PoolManager.json')
import pmdiff as P
from pyevm import World
from evm import keccak, MASK
code = P.fetch_code(); PM = int(P.PM, 16)
w = lambda x: (x & MASK).to_bytes(32, 'big'); sel = P.sel
S = {k: sel(v) for k, v in dict(bal='balanceOf(address,uint256)', tr='transfer(address,uint256,uint256)', tf='transferFrom(address,address,uint256,uint256)',
     ap='approve(address,uint256,uint256)', al='allowance(address,address,uint256)', op='setOperator(address,bool)', iso='isOperator(address,address)').items()}
def slot2(base, a, b): return int.from_bytes(keccak(w(b) + keccak(w(a) + w(base))), 'big')
def slot3(base, a, b, c): return int.from_bytes(keccak(w(c) + keccak(w(b) + keccak(w(a) + w(base)))), 'big')
def call(wd, frm, data):
    ok, ret = wd.call(frm, PM, 0, data, False, 0); return ok, ret
A, B = 0xA11CE, 0xB0B
# find the balanceOf base slot
wd = World({PM: code}); base = None
for k in range(12):
    wd.storage[(PM, slot2(k, A, 7))] = 1000 + k
for k in range(12):
    pass
ok, ret = call(wd, A, S['bal'] + w(A) + w(7)); v = int.from_bytes(ret, 'big'); base = v - 1000
assert 0 <= base < 12; print('balanceOf base slot', base)
wd = World({PM: code}); wd.storage[(PM, slot2(base - 1, A, B))] = 1; ok, ret = call(wd, A, S['iso'] + w(A) + w(B)); obase = base - 1 if int.from_bytes(ret, 'big') == 1 else None
abase = base + 1
print('isOperator base', obase, 'allowance base', abase)
rnd = random.Random(9); results = []; bad = 0
for i in range(3000):
    wd = World({PM: code}); idv = rnd.choice([0, 1, rnd.getrandbits(160), rnd.getrandbits(256)])
    bal = rnd.choice([0, 1, rnd.getrandbits(64), rnd.getrandbits(255), MASK]); amt = rnd.choice([0, 1, bal, (bal + 1) & MASK, rnd.getrandbits(64), bal // 2])
    wd.storage[(PM, slot2(base, A, idv))] = bal
    kind = rnd.choice(['transfer', 'transferFrom-self', 'transferFrom-operator', 'transferFrom-allowance', 'transferFrom-maxallowance'])
    caller = A
    if kind == 'transfer': data = S['tr'] + w(A) + w(idv) + w(amt)
    else:
        data = S['tf'] + w(A) + w(A) + w(idv) + w(amt)
        if kind != 'transferFrom-self': caller = B
        if kind == 'transferFrom-operator': wd.storage[(PM, slot2(obase, A, B))] = 1
        allowed = rnd.choice([amt, amt + 5, MASK, amt - 1 if amt else 0]) if 'allowance' in kind else 0
        if kind == 'transferFrom-maxallowance': allowed = MASK
        allowed &= MASK
        if 'allowance' in kind: wd.storage[(PM, slot3(abase, A, B, idv))] = allowed & MASK
    ok, ret = call(wd, caller, data)
    # expected from the source: balance -= amount (checked), then += amount (checked); allowance -= amount unless max (checked)
    exp_ok = amt <= bal
    if kind in ('transferFrom-allowance',) and allowed != MASK and amt > allowed: exp_ok = False
    after = int.from_bytes(call(wd, A, S['bal'] + w(A) + w(idv))[1], 'big')
    exp_after = bal
    good = (ok == exp_ok) and (after == exp_after) and (not ok or ret == w(1))
    if 'allowance' in kind:
        al = int.from_bytes(call(wd, A, S['al'] + w(A) + w(B) + w(idv))[1], 'big')
        exp_al = (allowed if (not ok or allowed == MASK) else allowed - amt) & MASK
        good = good and al == exp_al
    if not good: bad += 1; results.append(dict(i=i, kind=kind, bal=hex(bal), amt=hex(amt), ok=ok, after=hex(after)))
summary = dict(cases=3000, mismatches=bad, balanceOfBase=base, examples=results[:10])
json.dump(summary, open('coincide.json', 'w'), indent=1); print(summary)
