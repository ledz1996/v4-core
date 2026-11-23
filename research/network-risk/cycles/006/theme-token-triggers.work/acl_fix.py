# Second pass for tokens whose access list could not be read in discover.py: more endpoints, zero gas price, a funded sender.
import sys, json, gzip, os
from base import *
from tokcode import parse
from discover import rr, SLOTS
MORE = {480: ['https://480.rpc.thirdweb.com'], 42161: ['https://arbitrum-one-rpc.publicnode.com', 'https://arbitrum.drpc.org', 'https://42161.rpc.thirdweb.com', 'https://1rpc.io/arb'],
        56: ['https://bsc-rpc.publicnode.com', 'https://56.rpc.thirdweb.com', 'https://bsc.drpc.org'], 1: ['https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org', 'https://1.rpc.thirdweb.com'],
        8453: ['https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://8453.rpc.thirdweb.com'], 137: ['https://polygon-bor-rpc.publicnode.com', 'https://137.rpc.thirdweb.com'],
        43114: ['https://avalanche-c-chain-rpc.publicnode.com', 'https://avalanche.drpc.org']}
def acl_of(cid, t, pm):
    last = None
    for u in MORE.get(cid, []) + urls2(cid):
        for tx in ({'from': A, 'gasPrice': '0x0'}, {'from': A}, {'from': '0x000000000000000000000000000000000000dead'}, {'from': pm}, {'from': '0xba876237b0f021a6c6d852d6c26e107997cc5e81'}):
            tx = dict(tx, to=t, data=sel('balanceOf(address)') + adr(pm))
            try:
                j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_createAccessList', 'params': [tx, 'latest']}, timeout=40, tries=2)
            except Exception as e: last = str(e)[:100]; time.sleep(1.5); break
            if 'result' in j and 'accessList' in j['result']: return j['result']
            last = str(j.get('error'))[:120]
            if 'not exist' in last or 'not available' in last or 'Only core' in last: break
    return {'error': last}
def run(cid):
    fn = os.path.join(RAW6, 'discover_%d.json.gz' % cid); d = jz(fn); pm = net(cid)['poolManager'].lower(); fixed = 0
    for t, o in d.items():
        if o.get('acl') or 'err' in o: continue
        acl = acl_of(cid, t, pm)
        if 'accessList' not in acl: o['aclErr'] = str(acl)[:120]; continue
        o['acl'] = True; fixed += 1; o.pop('aclErr', None)
        for e in acl['accessList']:
            a = e['address'].lower()
            if a == t or int(a, 16) <= 0xffff or a in o['rel']: continue
            c2 = rr(cid, 'eth_getCode', [a, 'latest'])
            if isinstance(c2, str) and len(c2) > 2:
                o['rel'][a] = dict(kind='acl', size=len(c2) // 2 - 1, sels=parse(c2)['sels'])
                v = rr(cid, 'eth_getStorageAt', [a, SLOTS[0], 'latest'])
                if isinstance(v, str) and int(v, 16) and int(v, 16) < 2 ** 160:
                    a3 = '0x%040x' % int(v, 16)
                    if a3 not in o['rel']:
                        c3 = rr(cid, 'eth_getCode', [a3, 'latest'])
                        if isinstance(c3, str) and len(c3) > 2: o['rel'][a3] = dict(kind='impl-of:' + a, size=len(c3) // 2 - 1, sels=parse(c3)['sels'])
    json.dump(d, gzip.open(fn, 'wt'))
    left = [(t, o.get('aclErr')) for t, o in d.items() if not o.get('acl')]
    print(cid, 'fixed', fixed, 'left', len(left), left[:3], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
