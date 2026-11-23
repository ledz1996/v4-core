# FOLD (lead L-399): every bid of the claim source auction. Which bids have the PoolManager (or any contract that could pass
# tokens on) as owner, and how many are not exited or not claimed.
import json, os
from concurrent.futures import ThreadPoolExecutor
from base import *
CS = '0x687cc38d8279df3352b64cf3ec1fe8e033933595'; pm = net(1)['poolManager'].lower()
n = int(ecall(1, CS, sel('nextBidId()')), 16); print('nextBidId', n)
MC = '0xcA11bde05977b3631167028862bE2a173976CA11'
# aggregate3((address,bool,bytes)[])
def chunk(i):
    ids = list(range(i, min(n, i + 300)))
    calls = [(CS, sel('bids(uint256)')[2:] + u256(k)) for k in ids]
    head = sel('aggregate3((address,bool,bytes)[])')[2:] + u256(0x20) + u256(len(calls))
    offs = []; body = ''
    for to, cd in calls:
        offs.append(len(body) // 2)
        b = bytes.fromhex(cd)
        body += adr(to) + u256(1) + u256(0x60) + u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
    data = '0x' + head + ''.join(u256(32 * len(calls) + o) for o in offs) + body
    r = ecall(1, MC, data, gas=100_000_000)
    raw = bytes.fromhex(r[2:]); out = []
    base = 64; cnt = int.from_bytes(raw[32:64], 'big')
    for q in range(cnt):
        off = int.from_bytes(raw[base + 32 * q: base + 32 * q + 32], 'big') + base
        ok = int.from_bytes(raw[off:off + 32], 'big'); ln = int.from_bytes(raw[off + 64:off + 96], 'big'); dat = raw[off + 96: off + 96 + ln]
        w = [int.from_bytes(dat[32 * m:32 * m + 32], 'big') for m in range(7)] if ln >= 224 else None
        out.append((ids[q], ok, w))
    return out
rows = []
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(chunk, range(0, n, 300)): rows += res
bad = [r for r in rows if not r[1] or r[2] is None]
notex = [r for r in rows if r[2] and r[2][2] == 0]
unclaimed = [r for r in rows if r[2] and r[2][2] != 0 and r[2][6] > 0]
pmb = [r for r in rows if r[2] and ('0x%040x' % r[2][4]) == pm]
print('bids', len(rows), 'unreadable', len(bad), 'not exited', len(notex), 'exited with tokens still unclaimed', len(unclaimed), 'owner is PoolManager', len(pmb))
print('unclaimed tokens total', sum(r[2][6] for r in unclaimed) / 1e18)
print('not exited:', [(r[0], '0x%040x' % r[2][4], r[2][5] >> 96) for r in notex])
json.dump(dict(nextBidId=n, notExited=[(r[0], '0x%040x' % r[2][4], str(r[2][5] >> 96)) for r in notex], unclaimed=[(r[0], '0x%040x' % r[2][4], str(r[2][6])) for r in unclaimed], ownerPM=[r[0] for r in pmb]), open(os.path.join(RAW6, 'fold_bids.json'), 'w'))
owners = sorted({'0x%040x' % r[2][4] for r in notex + unclaimed})
print('owners of open bids', len(owners))
