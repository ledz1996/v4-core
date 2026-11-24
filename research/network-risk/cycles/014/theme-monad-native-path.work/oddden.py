"""FullMath.mulDiv (src/libraries/FullMath.sol:21-100) with the high word prod1 off by one, for odd and even
denominators, on inputs that take the 512 bit branch. Shows which denominators make a MULMOD(a,b,2^256-1)
fault visible in the result."""
import sys, random, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from evm import MASK
def muldiv_perturbed(a, b, den, dp):
    prod0 = m.mul(a, b); mm = (m.mulmod(a, b, MASK) + dp) % MASK
    prod1 = m.sub(m.sub(mm, prod0), m.lt(mm, prod0))
    if not den > prod1: return 'revert'
    if prod1 == 0: return m.div(prod0, den)
    r = m.mulmod(a, b, den); prod1 = m.sub(prod1, m.gt(r, prod0)); prod0 = m.sub(prod0, r)
    twos = m.sub(0, den) & den; den //= twos; prod0 //= twos; twos = m.add(m.div(m.sub(0, twos), twos), 1)
    prod0 |= m.mul(prod1, twos); inv = m.mul(3, den) ^ 2
    for _ in range(6): inv = m.mul(inv, m.sub(2, m.mul(den, inv)))
    return m.mul(prod0, inv)
rnd = random.Random(5); out = {'odd': [0, 0], 'even': [0, 0]}
while sum(v[0] for v in out.values()) < 400000:
    a, b = rnd.getrandbits(256), rnd.getrandbits(rnd.randrange(64, 257)); den = rnd.getrandbits(256) | (1 << 255)
    if rnd.random() < 0.5: den &= ~1
    else: den |= 1
    if (a * b) >> 256 == 0 or (a * b) // den > MASK: continue
    k = 'odd' if den & 1 else 'even'; out[k][0] += 1
    if muldiv_perturbed(a, b, den, 1) != (a * b) // den: out[k][1] += 1
print(json.dumps({'casesAndWrongResults': out}))
json.dump({'casesAndWrongResults': out}, open('oddden.json', 'w'))
