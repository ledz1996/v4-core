"""Pool state words of 13 live Avalanche pools read under both indexes that differ in bit 248, through
eth_getStorageAt and through extsload; state override behaviour of `state` (raw SetStorage) and `stateDiff`
(SetState with the key transformation) on a key with bit 248 set; availability of raw trie readers.
Usage: python3 probe2.py <pools.json> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, keccak
URL = 'https://api.avax.network/ext/bc/C/rpc'; PM = '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
B = 1 << 248; M = (1 << 256) - 1
pools = json.load(open(sys.argv[1]))['pools']
def h(x): return '0x%064x' % x
def q(m, p):
    try: return rpc(URL, m, p, timeout=60)
    except Exception as e: return 'ERR ' + str(e)
res = {'clientVersion': q('web3_clientVersion', [])}
blk = q('eth_blockNumber', []); res['block'] = int(blk, 16)
rows = []
for pid in pools:
    base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
    for off in range(4):
        s = (base + off) & M
        r = {'pool': pid, 'offset': off, 'slot': h(s), 'bit248': bool(s & B)}
        r['getStorageAt'] = q('eth_getStorageAt', [PM, h(s), blk])
        r['getStorageAtFlipped'] = q('eth_getStorageAt', [PM, h(s ^ B), blk])
        r['extsload'] = q('eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + h(s)[2:]}, blk])
        r['extsloadFlipped'] = q('eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + h(s ^ B)[2:]}, blk])
        r['allEqual'] = len({r['getStorageAt'], r['getStorageAtFlipped'], r['extsload'], r['extsloadFlipped']}) == 1
        r['nonzero'] = r['getStorageAt'] != h(0)
        rows.append(r)
res['rows'] = rows
res['summary'] = {'words': len(rows), 'withBit248': sum(r['bit248'] for r in rows), 'allEqual': sum(r['allEqual'] for r in rows), 'nonzero': sum(r['nonzero'] for r in rows)}
# overrides on a probe key with bit 248 set and on its twin
K1 = B | 0x1234; K0 = 0x1234; V = h(0xabcdef)
ov = {}
for nm, field, key in (('state K1(bit set)', 'state', K1), ('state K0(bit clear)', 'state', K0), ('stateDiff K1(bit set)', 'stateDiff', K1), ('stateDiff K0(bit clear)', 'stateDiff', K0)):
    for rk, rkey in (('read K1', K1), ('read K0', K0)):
        ov[nm + ' ' + rk] = q('eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + h(rkey)[2:]}, blk, {PM: {field: {h(key): V}}}])
    ov[nm + ' owner slot 0 after override'] = q('eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + h(0)[2:]}, blk, {PM: {field: {h(key): V}}}])
res['overrides'] = ov
res['rawReaders'] = {
    'eth_getProof': q('eth_getProof', [PM, [h(B)], blk]),
    'debug_storageRangeAt': q('debug_storageRangeAt', ['latest', 0, PM, h(0), 4]),
    'debug_dumpBlock': str(q('debug_dumpBlock', [blk]))[:300],
    'debug_accountRange': str(q('debug_accountRange', [blk, h(0), 1, True, True, False]))[:300],
}
res['clientVersionEnd'] = q('web3_clientVersion', [])
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(json.dumps(res['summary'])); print(json.dumps(ov, indent=1)); print(json.dumps(res['rawReaders'], indent=1))
