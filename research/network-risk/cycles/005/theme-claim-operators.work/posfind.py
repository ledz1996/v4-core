# Find positions held through the PositionManager in pools of a given currency: Initialize logs name the pool ids,
# ModifyLiquidity logs with sender = PositionManager carry the token id in the salt.
import sys, json, os
from lib import *
from fetch import getlogs_range
from config import CFG
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
ML = '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec'
def find(cid, tok, lo=None):
    n = net(cid); pm = n['poolManager']; posm = n['contracts']['PositionManager']; u, ch = CFG[cid]['init'], CFG[cid]['initChunk']
    lg = json.load(open(os.path.join(HERE, 'raw', 'logs_%d.json' % cid))); lo = lo or lg['fromBlock']; hi = lg['toBlock']
    pools = []
    for pos in (2, 3):
        t = [INIT, None, None, None]; t[pos] = pad_addr(tok)
        getlogs_range(u, {'address': pm, 'topics': t}, lo, hi, ch, workers=3, on_logs=pools.extend)
    out = []
    for p in pools:
        d = bytes.fromhex(p['data'][2:])
        key = dict(id=p['topics'][1], c0='0x' + p['topics'][2][-40:], c1='0x' + p['topics'][3][-40:], fee=int.from_bytes(d[0:32], 'big'), ts=int.from_bytes(d[32:64], 'big'), hooks='0x' + d[64:96][-20:].hex(), block=int(p['blockNumber'], 16))
        ml = []
        getlogs_range(u, {'address': pm, 'topics': [ML, key['id'], pad_addr(posm)]}, key['block'], hi, ch, workers=3, on_logs=ml.extend)
        liq = {}
        for l in ml:
            dd = bytes.fromhex(l['data'][2:]); tid = int.from_bytes(dd[96:128], 'big'); dl = int.from_bytes(dd[64:96], 'big', signed=True)
            e = liq.setdefault(tid, dict(liq=0, tl=int.from_bytes(dd[0:32], 'big', signed=True), tu=int.from_bytes(dd[32:64], 'big', signed=True))); e['liq'] += dl
        key['positions'] = {str(k): v for k, v in liq.items() if v['liq'] > 0}
        out.append(key)
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1]); r = find(cid, sys.argv[2])
    json.dump(r, open(os.path.join(HERE, 'raw', 'positions_%d_%s.json' % (cid, sys.argv[2].lower())), 'w'))
    for k in r: print(k['id'][:14], k['c0'], k['c1'], k['fee'], k['ts'], k['hooks'], 'open positions via PositionManager', len(k['positions']), sorted(k['positions'].items(), key=lambda kv: -kv[1]['liq'])[:3])
