"""Debug: for the mismatches of a stage B run on pools keyed by getPool(uint24), list the pool's events in that block, the parent slot0
and liquidity, and the tx's other logs. Read only."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
U = 'https://rpc.purroofgroup.com'
R = json.load(open(sys.argv[1])); P = json.load(open('raw/pools999.json'))['pools']
ev = {}
want = {(m['pool'], m['block']) for m in R['mismatches'] if P[m['pool']].get('getPool', 'u24') == 'u24'}
for line in open('raw/logs999.jsonl'):
    for r in json.loads(line)['rows']:
        if (r[4], r[1]) in want: ev.setdefault((r[4], r[1]), []).append(r)
for (pool, b), rows in ev.items():
    s0 = rpc(U, 'eth_call', [{'to': pool, 'data': '0x3850c7bd'}, hex(b - 1)]); L = rpc(U, 'eth_call', [{'to': pool, 'data': '0x1a686502'}, hex(b - 1)])
    fee = rpc(U, 'eth_call', [{'to': pool, 'data': '0xddca3f43'}, hex(b - 1)])
    print('==', pool, b, P[pool]['factory'], 'fee', P[pool]['fee'], int(fee, 16), 'parent price', int(s0[2:66], 16), 'liq', int(L, 16), 'slot0words', len(s0) // 64)
    for r in sorted(rows, key=lambda r: r[2]): print('  ', r)
    tx = rows[0][3]
    rc = rpc(U, 'eth_getTransactionReceipt', [tx])
    print('   logs in tx', len(rc['logs']), sorted({l['address'] for l in rc['logs']})[:8])
