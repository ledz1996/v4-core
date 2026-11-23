# The other Alpaca vault tokens that the BNB Smart Chain PoolManager holds: every selector of proxy and implementation, PoolManager as argument.
import json, os, collections
from base import *
import holder
sys.path.insert(0, W6C)
from tokcode import parse
cid = 56; pm = net(cid)['poolManager'].lower()
T = {'ibBNB': '0xd7d069493685a581d27824fc46eda46b7efc0063', 'ibUSDT': '0x158da805682bdc8ee32d52833ad41e74bb951e59', 'ibALPACA': '0xf1be8ecc990cbcb90e166b71e368299f0116d421', 'ibCAKE': '0xff693450dda65df7dd6f45b4472655a986b147eb', 'ibBUSD': '0x7c9e73d4c71dae564d41f78d56439bb4ba87592f'}
u = 'https://bsc-dataseed1.bnbchain.org'
now = int(time.time()); far = now + 5 * 365 * 86400; out = {}
for nm, t in T.items():
    c = rpc(u, 'eth_getCode', [t, 'latest']); sels = set(parse(c)['sels'])
    v = rpc(u, 'eth_getStorageAt', [t, '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', 'latest']); impl = '0x%040x' % int(v, 16)
    if int(v, 16): sels |= set(parse(rpc(u, 'eth_getCode', [impl, 'latest']))['sels'])
    b = int(ecall(cid, t, sel('balanceOf(address)') + adr(pm)), 16); amt = b // 3
    pl = holder.plan(t, sorted(sels), pm, amt, far)
    hits = []; ntr = 0; nacc = 0
    for i in range(0, len(pl), 40):
        ch = [('BASE', t, sel('balanceOf(address)')[2:] + adr(pm))] + pl[i:i + 40]
        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(holder.item(adr(tg) + cd) for n_, tg, cd in ch)
        r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=120_000_000, tries=6)
        ws = [[int(r[2 + 512 * q + 64 * m: 66 + 512 * q + 64 * m], 16) for m in range(8)] for q in range(len(ch))]
        for (n_, tg, cd), w in zip(ch[1:], ws[1:]):
            ntr += 1; nacc += w[2]
            k = holder.classify(ws[0], w)
            if k and k != 'raise-paid': hits.append((k, n_, w[3] - ws[0][3], w[4] - ws[0][4]))
    out[nm] = dict(token=t, impl=impl, selectors=len(sels), hasClaimFor='ddeae033' in sels, balance=str(b), trials=ntr, accepted=nacc, hits=hits)
    print(nm, t, 'impl', impl, 'selectors', len(sels), 'claimFor present', 'ddeae033' in sels, 'balance', b, 'trials', ntr, 'accepted', nacc, 'hits', hits)
json.dump(out, open(os.path.join(RAW7, 'alpaca_56.json'), 'w'), indent=1)
