"""MULMOD sequences aimed at the one-entry reciprocal memo of bor v2.12.0-beta (core/vm/mulmod_memo.go):
runs of one full-width modulus (memo hits), alternation of two full-width moduli and of a full-width with a
narrow modulus (misses and bypasses), moduli that differ from the previous one in a single limb or a single
bit (the memo compares all four limbs), 2^256-1 as FullMath.mulDiv uses it, and the FullMath sequence
mulmod(a,b,not(0)) then mulmod(a,b,d) with a full-width d. All records go through the opdiff battery
dispatcher in one eth_call, so the memo state carries from record to record as it would inside one EVM.
Usage: python3 mulmod_memo.py <out.json>"""
import sys, os, json, random
T = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, T)
import battery as B
M = (1 << 256) - 1
rnd = random.Random(12_2026_11_24)
def full(): return rnd.getrandbits(256) | (1 << 255) if rnd.random() < .5 else rnd.getrandbits(256) | (1 << 193)
V = []
def mm(a, b, m): V.append(('MULMOD', a & M, b & M, m & M))
for _ in range(400):
    m1, m2 = full(), full()
    for k in range(rnd.randint(2, 6)): mm(rnd.getrandbits(256), rnd.getrandbits(256), m1)          # hits
    mm(rnd.getrandbits(256), rnd.getrandbits(256), m2); mm(rnd.getrandbits(256), rnd.getrandbits(256), m1)  # alternate
    limb = rnd.randrange(4); m3 = m1 ^ (rnd.getrandbits(64) << (64 * limb)) or 1
    mm(rnd.getrandbits(256), rnd.getrandbits(256), m3)                                           # one limb differs
    m4 = m1 ^ (1 << rnd.randrange(256)); mm(rnd.getrandbits(256), rnd.getrandbits(256), m4)     # one bit differs
    mm(rnd.getrandbits(256), rnd.getrandbits(256), rnd.getrandbits(190))                         # narrow, bypass
    mm(rnd.getrandbits(256), rnd.getrandbits(256), m4)                                           # back to memo entry
    mm(rnd.getrandbits(256), rnd.getrandbits(256), 0)                                            # zero modulus
    a, b = rnd.getrandbits(256), rnd.getrandbits(256)
    mm(a, b, M); mm(a, b, m1); mm(a, b, M); mm(M, M, M); mm(M - 1, M, M)                         # FullMath shapes
    mm(m1, m1, m1); mm(m1 - 1, m1 + 1, m1); mm(a, 1, m1); mm(0, b, m1)
    V.append(('MULDIV512', a, b, m1))
if __name__ == '__main__':
    code = B.dispatcher()
    EP = [('Polygon bor v2.11.1 publicnode', 'https://polygon-bor-rpc.publicnode.com'), ('Polygon bor v2.11.1 quiknode', 'https://rpc-mainnet.matic.quiknode.pro'),
          ('BSC geth dataseed1', 'https://bsc-dataseed1.bnbchain.org'), ('BSC reth-bsc', 'https://bsc-rpc.publicnode.com'),
          ('Avalanche api', 'https://api.avax.network/ext/bc/C/rpc'), ('Ethereum publicnode', 'https://ethereum-rpc.publicnode.com')]
    out = {'vectors': len(V), 'results': []}
    for name, url in EP:
        done, bad, errors = B.run(url, code, V, size=500)
        print(name, 'ran', done, 'of', len(V), 'mismatches', len(bad), 'errors', len(errors), errors[:1], flush=True)
        out['results'].append({'name': name, 'rpc': url, 'ran': done, 'mismatches': bad[:50], 'errors': errors[:5]})
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
