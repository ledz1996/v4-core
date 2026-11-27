# Opcode skeleton (PUSH data removed) of each official router and PositionManager, to match unverified deployments to verified ones.
# Also counts PUSH4 0xa5841194 (sync) and 0x11da60b4 (settle) in the code.
import sys, json, os, hashlib, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from config import CFG
S_ = json.load(open('out/periphery_src.json'))
def skel(code):
    b = bytes.fromhex(code[2:]); i = 0; out = bytearray(); p4 = []
    while i < len(b):
        op = b[i]; out.append(op)
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f
            if n == 4: p4.append(b[i+1:i+5].hex())
            i += n
        i += 1
    return hashlib.sha256(bytes(out)).hexdigest()[:16], p4
def one(x):
    n = net(x['chainId']); urls = [n['rpc']] + CFG[x['chainId']]['state']
    for u in urls:
        try:
            c = rpc(u, 'eth_getCode', [x['addr'], 'latest'])
            ver = rpc(u, 'web3_clientVersion', [])
            sk, p4 = skel(c)
            return dict(x, url=u, client=ver, codeLen=(len(c) - 2) // 2, skeleton=sk, sync4=p4.count('a5841194'), settle4=p4.count('11da60b4'))
        except Exception as e: last = str(e)[:100]
    return dict(x, err=last)
with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(one, S_))
by = {}
for r in res:
    if r.get('verified') and 'skeleton' in r: by.setdefault(r['skeleton'], []).append('%d:%s' % (r['chainId'], r['addr'][:10]))
for r in res: r['skeletonMatchesVerified'] = by.get(r.get('skeleton'), [])
for r in res: r.pop('settleSites', None)
json.dump(res, open('out/periphery_code.json', 'w'), indent=1)
for r in res: print(r['chainId'], r['name'][:22].ljust(22), r['addr'][:10], 'ver' if r.get('verified') else 'UNV', r.get('codeLen'), r.get('skeleton'), 'sync', r.get('sync4'), 'settle', r.get('settle4'), 'match', r['skeletonMatchesVerified'][:2], r.get('err', ''))
