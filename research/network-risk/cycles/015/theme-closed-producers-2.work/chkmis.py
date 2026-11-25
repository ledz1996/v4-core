"""For every stage B mismatch, list the pool's logs in that block whose topic the collector does not read, and test whether
applying a 0xd78218c0 Mint variant (liquidity in data word 2, ticks in topics 2 and 3) gives the logged liquidity. Read only.
Usage: chkmis.py <stageB json>..."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
U = 'https://rpc.purroofgroup.com'
KNOWN = {'0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67': 'Swap', '0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde': 'Mint',
         '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c': 'Burn', '0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0': 'Collect'}
def s(x): return x - (1 << 256) if x >> 255 else x
for f in sys.argv[1:]:
    for m in json.load(open(f))['mismatches']:
        pool, b = m['pool'], m['block']
        L0 = int(rpc(U, 'eth_call', [{'to': pool, 'data': '0x1a686502'}, hex(b - 1)]), 16)
        t0 = s(int(rpc(U, 'eth_call', [{'to': pool, 'data': '0x3850c7bd'}, hex(b - 1)])[66:130], 16))
        lg = rpc(U, 'eth_getLogs', [{'address': pool, 'fromBlock': hex(b), 'toBlock': hex(b)}])
        other = [l for l in lg if l['topics'][0] not in KNOWN]
        liq = L0; tick = t0; note = []
        for l in lg:
            if int(l['logIndex'], 16) > m['logIndex']: break
            t = l['topics'][0]; d = l['data'][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
            if t in KNOWN and KNOWN[t] == 'Swap' and int(l['logIndex'], 16) < m['logIndex']:
                liq = w[3]; tick = s(w[4]); continue
            if len(l['topics']) == 4 and t[:10] in ('0xd78218c0', '0x7a53080b', '0x0c396cd9'):
                tl, tu = s(int(l['topics'][2], 16)), s(int(l['topics'][3], 16))
                amt = w[2] if t[:10] == '0xd78218c0' else (w[1] if t[:10] == '0x7a53080b' else -w[0])
                if tl <= tick < tu: liq += amt
                note.append((t[:10], tl, tu, amt))
        print(m['tx'], b, 'otherTopics', sorted({l['topics'][0][:10] for l in other}), 'liq before swap with all events', liq, 'logged after', m['liq'], note)
