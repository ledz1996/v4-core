"""Critic check, cycle 6. Exhaustive walk of the settlement functions as written in
src/PoolManager.sol:279-378 against a native asset that has an ERC-20 face. Model only, no chain access.

State: B = native balance of the PoolManager in wei, W = wallet of the caller in wei, d0 and dF = deltas of
the caller under address(0) and under the face id, c0 and cF = ERC-6909 claims of the caller, slot = synced
currency (0 or the face), R = synced reserves.
k = wei per face unit (1 for the CELO token, 3 as a stand in for the 10^12 of the Arc token at 0x3600...).
pay_out = whether face.transfer from the PoolManager works (False models 0x1010 on Polygon).
sub_unit = whether native value can reach the PoolManager outside settle in amounts below one face unit.

A gain state is one where every delta is zero and wallet plus claims exceed the starting wallet.
Usage: python3 -I face_model.py <depth>"""
import sys
from collections import deque

def run(k, pay_out, sub_unit, depth, amts=(1, 2)):
    B0, W0 = 12, 12
    start = (B0, W0, 0, 0, 0, 0, 0, 0)
    seen = {start: None}
    q = deque([(start, 0)])
    hits = []
    while q:
        s, n = q.popleft()
        B, W, d0, dF, c0, cF, slot, R = s
        if n > 0 and d0 == 0 and dF == 0 and W + c0 + cF * k > W0:
            hits.append(s)
        if n == depth:
            continue
        nxt = []
        nxt.append(('sync(0)', (B, W, d0, dF, c0, cF, 0, R)))                    # line 283: resets the slot only
        nxt.append(('sync(face)', (B, W, d0, dF, c0, cF, 1, B // k)))            # lines 285-286
        for v in (0,) + tuple(amts):
            if slot == 0:
                if v <= W:                                                         # lines 353-354 and 364
                    nxt.append((f'settle value {v}', (B + v, W - v, d0 + v, dF, c0, cF, 0, R)))
            elif v == 0:                                                           # line 356 rejects value
                paid = B // k - R                                                  # lines 358-360, checked
                if paid >= 0:
                    nxt.append(('settle value 0', (B, W, d0, dF + paid, c0, cF, 0, R)))   # line 361 resets
        for a in amts:
            if B >= a:
                nxt.append((f'take native {a}', (B - a, W + a, d0 - a, dF, c0, cF, slot, R)))
            if pay_out and B >= a * k:
                nxt.append((f'take face {a}', (B - a * k, W + a * k, d0, dF - a, c0, cF, slot, R)))
            if W >= a * k:
                nxt.append((f'face transfer in {a}', (B + a * k, W - a * k, d0, dF, c0, cF, slot, R)))
            if sub_unit and W >= a:
                nxt.append((f'forced value {a}', (B + a, W - a, d0, dF, c0, cF, slot, R)))
            nxt.append((f'mint native {a}', (B, W, d0 - a, dF, c0 + a, cF, slot, R)))
            nxt.append((f'mint face {a}', (B, W, d0, dF - a, c0, cF + a, slot, R)))
            if c0 >= a:
                nxt.append((f'burn native {a}', (B, W, d0 + a, dF, c0 - a, cF, slot, R)))
            if cF >= a:
                nxt.append((f'burn face {a}', (B, W, d0, dF + a, c0, cF - a, slot, R)))
        if d0 > 0:
            nxt.append(('clear native', (B, W, 0, dF, c0, cF, slot, R)))
        if dF > 0:
            nxt.append(('clear face', (B, W, d0, 0, c0, cF, slot, R)))
        for name, t in nxt:
            if abs(t[2]) > 6 or abs(t[3]) > 6 or t[4] > 6 or t[5] > 6:
                continue
            if t not in seen:
                seen[t] = (s, name)
                q.append((t, n + 1))
    return seen, hits, W0

depth = int(sys.argv[1]) if len(sys.argv) > 1 else 9
cases = (
    (1, True, True, 'Celo shape (1 wei per unit, face pays out, forced value allowed)'),
    (1, False, True, 'Polygon shape (face mirrors the balance, face payout fails, forced value allowed)'),
    (3, True, False, 'Arc shape (3 wei per unit, inflows in whole units or through settle only)'),
    (3, True, True, 'Arc shape (3 wei per unit, forced value below one unit allowed)'),
)
for k, pay_out, sub_unit, label in cases:
    seen, hits, W0 = run(k, pay_out, sub_unit, depth)
    best = max((h[1] + h[4] + h[5] * k - W0 for h in hits), default=0)
    print(f'{label}: depth {depth}, states {len(seen)}, gain states {len(hits)}, largest gain {best} wei')
    for h in hits[:2]:
        path = []
        s = h
        while seen[s]:
            s, name = seen[s]
            path.append(name)
        print('   example:', ' -> '.join(reversed(path)), '| end state B,W,d0,dF,c0,cF,slot,R =', h)
