"""Read-only probes of the multicoin (asset) partition of the PoolManager account on the Avalanche C-Chain.

1. web3_clientVersion before and after.
2. eth_call to the NativeAssetBalance (0x01..01) and NativeAssetCall (0x01..02) precompiles and the genesis
   contract (0x01..00), from the PoolManager address and from a plain address.
3. eth_getProof of the PoolManager account (raw trie keys, no key transformation in libevm's GetProof):
   the account leaf is decoded to read the held-X-chain-asset extra; for slots 0..6 and for the pool state
   words of up to 12 live pools, both the EVM key (bit 248 cleared) and its asset twin (bit 248 set) are proved.
4. eth_getStorageAt for the same keys, to show the RPC applies the transformation.

Usage: python3 probe.py <outdir>
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc, keccak

URL = 'https://api.avax.network/ext/bc/C/rpc'
PM = '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
PLAIN = '0x00000000000000000000000000000000000a11ce'
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
AVAX_ASSET = 'FvwEAhmxKfeiG8SnEvq42hc6whRyY3EFYAvebMqDNDGCgxN5Z'
B248 = 1 << 248
out = sys.argv[1]
log = []


def call(m, p):
    t = time.time()
    try:
        r = rpc(URL, m, p, timeout=60)
        ok = True
    except Exception as e:  # record the error text
        r = str(e); ok = False
    log.append({'method': m, 'params': p, 'ok': ok, 'result': r, 't': t})
    return r


def h32(x): return '0x%064x' % x


def rlp_decode(b):
    def item(i):
        x = b[i]
        if x < 0x80: return b[i:i + 1], i + 1
        if x < 0xb8: n = x - 0x80; return b[i + 1:i + 1 + n], i + 1 + n
        if x < 0xc0:
            ln = x - 0xb7; n = int.from_bytes(b[i + 1:i + 1 + ln], 'big'); s = i + 1 + ln; return b[s:s + n], s + n
        if x < 0xf8: n = x - 0xc0; s = i + 1
        else: ln = x - 0xf7; n = int.from_bytes(b[i + 1:i + 1 + ln], 'big'); s = i + 1 + ln
        lst = []; j = s
        while j < s + n:
            v, j = item(j); lst.append(v)
        return lst, s + n
    return item(0)[0]


res = {'clientVersionStart': call('web3_clientVersion', [])}
head = int(call('eth_blockNumber', []), 16); res['head'] = head
blk = hex(head)

# 2. precompile calls
asset = '00' * 31 + '01'
inbal = PM[2:] + asset
incall = PLAIN[2:] + asset + '%064x' % 0
pc = {}
for to, data in (('0x0100000000000000000000000000000000000000', ''),
                 ('0x0100000000000000000000000000000000000001', inbal),
                 ('0x0100000000000000000000000000000000000002', incall)):
    for frm in (PM, PLAIN):
        r = call('eth_call', [{'from': frm, 'to': to, 'data': '0x' + data, 'gas': '0x100000'}, blk])
        pc['%s from %s' % (to, frm)] = r
    pc['%s code' % to] = call('eth_getCode', [to, blk])
res['precompileCalls'] = pc

# live pools from Initialize logs
pools = []
lo = head - 2000
for k in range(40):
    r = call('eth_getLogs', [{'address': PM, 'topics': [INIT], 'fromBlock': hex(max(0, lo - 2047)), 'toBlock': hex(lo)}])
    if isinstance(r, list):
        for e in r:
            if e['topics'][1] not in pools: pools.append(e['topics'][1])
    lo -= 2048
    if len(pools) >= 12: break
res['poolIds'] = pools[:12]

# 3. proof
keys = []
for s in range(7): keys.append(('fixed slot %d' % s, s))
for pid in pools[:12]:
    base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
    for off, nm in ((0, 'slot0'), (1, 'feeGrowthGlobal0'), (2, 'feeGrowthGlobal1'), (3, 'liquidity')):
        keys.append(('%s %s' % (pid[:10], nm), (base + off) % (1 << 256)))
rows = []
allkeys = []
for nm, k in keys:
    evm = k & ~B248
    twin = k | B248
    allkeys += [h32(evm), h32(twin)]
    rows.append({'name': nm, 'slot': h32(k), 'bit248InSlot': bool(k & B248), 'evmKey': h32(evm), 'assetTwin': h32(twin)})
proofs = []
for i in range(0, len(allkeys), 20):
    p = call('eth_getProof', [PM, allkeys[i:i + 20], blk])
    proofs.append(p)
vals = {}
acct = None
for p in proofs:
    if isinstance(p, dict):
        acct = p
        for sp in p.get('storageProof', []):
            vals[int(sp['key'], 16)] = (sp['value'], len(sp['proof']))
for r in rows:
    r['proofEvmKey'] = vals.get(int(r['evmKey'], 16))
    r['proofAssetTwin'] = vals.get(int(r['assetTwin'], 16))
    r['getStorageAtSlot'] = call('eth_getStorageAt', [PM, r['slot'], blk])
    r['getStorageAtTwin'] = call('eth_getStorageAt', [PM, r['assetTwin'], blk])
    # extsload through the contract (selector of extsload(bytes32) = 0x1e2eaeaf)
    r['extsloadSlot'] = call('eth_call', [{'to': PM, 'data': '0x1e2eaeaf' + r['slot'][2:]}, blk])
res['keys'] = rows
if acct:
    res['account'] = {k: acct.get(k) for k in ('balance', 'nonce', 'storageHash', 'codeHash')}
    leaf = bytes.fromhex(acct['accountProof'][-1][2:])
    node = rlp_decode(leaf)
    val = rlp_decode(node[-1]) if isinstance(node, list) else None
    res['accountLeafFields'] = [x.hex() if isinstance(x, bytes) else x for x in val] if isinstance(val, list) else repr(val)
    res['accountLeafFieldCount'] = len(val) if isinstance(val, list) else None
# plain EOA and a known account for comparison of the leaf shape
for nm, a in (('plain', PLAIN), ('blackhole 0x0100..00', '0x0100000000000000000000000000000000000000')):
    p = call('eth_getProof', [a, [], blk])
    if isinstance(p, dict) and p.get('accountProof'):
        node = rlp_decode(bytes.fromhex(p['accountProof'][-1][2:]))
        try:
            val = rlp_decode(node[-1])
            res['leaf ' + nm] = [x.hex() if isinstance(x, bytes) else x for x in val]
        except Exception as e:
            res['leaf ' + nm] = 'not a leaf for this address (absent account): ' + str(e)
res['clientVersionEnd'] = call('web3_clientVersion', [])
json.dump(res, open(os.path.join(out, 'probe.json'), 'w'), indent=1)
json.dump(log, open(os.path.join(out, 'probe.rpc.log.json'), 'w'), indent=0)
print(json.dumps({k: v for k, v in res.items() if k != 'keys'}, indent=1)[:4000])
for r in rows: print(r['name'], r['bit248InSlot'], r['proofEvmKey'], r['proofAssetTwin'], r['getStorageAtSlot'][:20] if isinstance(r['getStorageAtSlot'], str) else r['getStorageAtSlot'], r['getStorageAtTwin'][:20] if isinstance(r['getStorageAtTwin'], str) else '')
