"""FullMath.sol:62,67,73 shapes (division by twos = 2^k, and (2^256 - 2^k) / 2^k) and TickMath.sol:104
(div(not(0), price)) through the transcribed holiman/uint256 master Div. Compared with Python integers."""
import sys, json, random
sys.path.insert(0, sys.argv[1]); import uint256_master_div as u
R=random.Random(5); bad=[]; n=0
for k in range(256):
    t=1<<k
    for X in [(1<<256)-t, (1<<256)-1, R.getrandbits(256), R.getrandbits(256)|t, t, t-1 if t>1 else 0, t+1]:
        X%=1<<256; n+=1
        if u.Div(u.limbs(X),u.limbs(t))!=X//t: bad.append([hex(X),k])
for i in range(20000):
    p=R.randrange(4295128739, 1461446703485210103287273052203988822378723970342)
    n+=1
    if u.Div(u.limbs((1<<256)-1),u.limbs(p))!=((1<<256)-1)//p: bad.append(['notzero/price',hex(p)])
json.dump({'cases':n,'mismatches':len(bad),'examples':bad[:10]},open(sys.argv[2],'w'),indent=1)
print('cases',n,'mismatches',len(bad))
