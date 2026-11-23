# Fetch verified source from Sourcify for a contract (and its EIP-1967 implementation) into a scratch directory. Read only.
import sys, json, os, requests
from lib import *
from config import CFG
OUT = '/tmp/claude-0/-home-user-v4-core/0b315df9-4a6b-5032-a881-24bad3c79fc5/scratchpad/src'
def fetch(cid, addr):
    u = 'https://sourcify.dev/server/v2/contract/%d/%s?fields=sources,abi,compilation' % (cid, addr)
    r = requests.get(u, timeout=40, headers={'user-agent': 'curl/8'})
    if r.status_code != 200: return None, u
    j = r.json(); d = os.path.join(OUT, '%d_%s' % (cid, addr.lower())); os.makedirs(d, exist_ok=True)
    for path, s in (j.get('sources') or {}).items():
        fn = os.path.join(d, path.replace('/', '__').replace('..', '_'))
        open(fn, 'w').write(s.get('content', ''))
    json.dump(j.get('abi'), open(os.path.join(d, 'abi.json'), 'w'))
    return dict(dir=d, name=(j.get('compilation') or {}).get('name'), files=len(j.get('sources') or {}), fns=sorted(a['name'] for a in (j.get('abi') or []) if a.get('type') == 'function')), u
def impl(cid, addr):
    u = CFG[cid]['state'][0]
    for slot in ('0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', '0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3', '0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50'):
        v = rpc(u, 'eth_getStorageAt', [addr, slot, 'latest'])
        if int(v, 16):
            a = '0x' + v[-40:]
            if slot.startswith('0xa3f0'):  # beacon
                a = '0x' + rpc(u, 'eth_call', [{'to': a, 'data': '0x5c60da1b'}, 'latest'])[-40:]
            return a
    return None
if __name__ == '__main__':
    cid = int(sys.argv[1]); a = sys.argv[2]
    print(fetch(cid, a)); i = impl(cid, a)
    if i: print('impl', i, fetch(cid, i))
