from realpm import *
LOCK='c090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23'
import keccak
def slot(name): return (int.from_bytes(keccak256(name.encode()),'big')-1).to_bytes(32,'big').hex()
print('lock slot',slot('Unlocked'),'currency slot',slot('Currency'),'count slot',slot('NonzeroDeltaCount'))
for chain in (143,4326):
    pm=PM[chain]
    ext=lambda s: sel('exttload(bytes32)')+s
    V=10**15
    recs=[('exttload lock',rec(1,pm,ext(slot('Unlocked')))),
          ('settle{value:V}',rec(0,pm,sel('settle()'),V)),
          ('exttload count',rec(1,pm,ext(slot('NonzeroDeltaCount')))),
          ('take(native,X,V)',rec(0,pm,sel('take(address,address,uint256)')+w(0)+w(int(X,16))+w(V))),
          ('exttload count',rec(1,pm,ext(slot('NonzeroDeltaCount')))),
          ('unlock again (must fail)',rec(0,pm,sel('unlock(bytes)')+w(0x20)+w(0))),
          ('sync(WRAPPER)',rec(0,pm,sel('sync(address)')+w(int({143:'0x3bd359C1119dA7Da1D913D1C4D2B7c461115433A',4326:'0x4200000000000000000000000000000000000006'}[chain],16)))),
          ('settle{value:1} with token synced (must fail)',rec(0,pm,sel('settle()'),1)),
          ('settle() zero',rec(0,pm,sel('settle()'))),
          ('exttload currency',rec(1,pm,ext(slot('Currency')))),
          ]
    for delegated in (False,True):
        res=unlock_inner(chain,[r[1] for r in recs],delegated=delegated)
        print('== chain',chain,'caller is','an EIP-7702 delegated account' if delegated else 'a contract')
        for (n,_),x in zip(recs,res): print(f'   {n:48}',(x.get('ok'),x.get('rds'),x.get('ret','')[:72]) if 'ok' in x else x)
    # after unlock returns: lock flag and a take outside
    post=[rec(1,pm,ext(slot('Unlocked'))),rec(1,pm,ext(slot('NonzeroDeltaCount'))),rec(0,pm,sel('take(address,address,uint256)')+w(0)+w(int(X,16))+w(1))]
    r=unlock_call(chain,[recs[1][1],recs[3][1]],post=post)
    print('   after unlock returned: [unlock ok, lock slot, count slot, take outside]',[(o['ok'],o['ret'][:8] if not o['ok'] else o['ret'][56:64]) for o in r.get('outer',[])] if 'outer' in r else r)
