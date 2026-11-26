"""Task 3 inputs, written in the replay format with the reference EVM's call tree (the recorder of sets2tx.py):
  t3-short.txt : PoolManager calldata seen in the six sets, up to three examples per selector, cut to every length and with each
                 head word replaced by offsets that point at or past the end of the calldata. Root call from an ordinary account
                 to the PoolManager, empty storage.
  t3-deleg.txt : up to three valid calldata per selector, run as PoolManager code in the storage context of another account
                 (DELEGATECALL); replay.cpp runs it with HX_SELF set to that account.
The inputs are enumerated, so there is no seed. Usage: PM_BUILD=... python3 t3gen.py <out dir>"""
import sys, os, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import sets2tx as S
P, pyevm = S.P, S.pyevm
PMI = S.PMI; EOA = 0xA11CE; SELF = 0xBEEF0000000000000000000000000000000BEEF0
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
code = P.fetch_code()
ex = collections.defaultdict(list)
for s in '123456':
    for line in open(f'{here}/../sets/s{s}/set{s}.txt'):
        t = line.split()
        if t[0] == 'N' and t[3] == '1' and t[12] != '-':
            d = bytes.fromhex(t[12]); sel = d[:4]
            if len(ex[sel]) < 3 and all(len(x) != len(d) for x in ex[sel]): ex[sel].append(d)
print(len(ex), 'selectors', sum(len(v) for v in ex.values()), 'examples')
def variants(d):
    n = len(d); seen = set()
    lens = list(range(0, n + 1)) if n <= 420 else list(range(0, 420)) + list(range(420, n + 1, 7)) + [n]
    for L in lens:
        v = d[:L]
        if v not in seen: seen.add(v); yield v
    nargs = (n - 4) // 32
    for k in range(min(nargs, 14)):
        for val in (n - 4 - 1, n - 4 - 16, n - 4 - 31, n - 4 - 32, n - 4, n - 4 + 1, n - 4 + 32, (1 << 64) - 1, (1 << 64), 1 << 255, (1 << 256) - 1, 0):
            v = d[:4 + 32 * k] + (val % (1 << 256)).to_bytes(32, 'big') + d[4 + 32 * k + 32:]
            if v not in seen: seen.add(v); yield v
st = collections.Counter(); n = 0
with open(f'{out}/t3-short.txt', 'w') as f:
    for sel, xs in ex.items():
        for d in xs:
            for v in variants(d):
                w = pyevm.World({PMI: code}); n += 1
                st[S.write_tx(f, f'short-{sel.hex()}-{n}', w, PMI, v, 2_000_000, caller=EOA)] += 1
print('short', dict(st))
st = collections.Counter()
with open(f'{out}/t3-deleg.txt', 'w') as f:
    for sel, xs in ex.items():
        for d in xs:
            w = pyevm.World({PMI: code}); n += 1
            st[S.write_tx(f, f'deleg-{sel.hex()}-{n}', w, PMI, d, 2_000_000, caller=EOA, delegate_from=SELF)] += 1
print('deleg', dict(st))
