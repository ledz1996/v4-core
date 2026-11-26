"""Pool census for one network: earlier Initialize rows plus raw/initext_<cid>, pool ids recomputed as keccak256(abi.encode(PoolKey))
with build/kec, then EXTCODESIZE of every distinct hook at one block through eth_call with a state-override helper.
Read only. usage: census.py <chainId> <url> [perCall]"""
import sys, json, gzip, struct, subprocess, time, collections, os
import numpy as np
from ep import rpc, NETS
cid, url = int(sys.argv[1]), sys.argv[2]; PER = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
C5 = '/home/user/v4-core/research/network-risk/cycles/005/theme-shared-hooks.work/raw/'
C6 = '/home/user/v4-core/research/network-risk/cycles/006/theme-currency-lists.work/raw/'
src = []
def load_json(fn):
    d = json.load(gzip.open(fn, 'rt')); src.append({'file': fn, 'lo': d['lo'], 'hi': d['hi'], 'rows': len(d['rows']), 'url': d['url']}); return d['rows']
if cid == 8453:
    # binary rows of cycle 6: [u32 windowStart][u32 count] + count * (u32 block, 32 id, 20 c0, 20 c1, 20 hooks, u24 fee, i24 ts)
    dt = np.dtype([('b', '>u4'), ('id', 'V32'), ('c0', 'V20'), ('c1', 'V20'), ('h', 'V20'), ('fee', 'V3'), ('ts', 'V3')])
    raw = np.fromfile(C6 + 'base_init.bin', dtype=np.uint8); parts = []; off = 0
    while off + 8 <= len(raw):
        a, n = struct.unpack('>II', raw[off:off + 8].tobytes()); off += 8
        parts.append(np.frombuffer(raw[off:off + 102 * n].tobytes(), dtype=dt)); off += 102 * n
    B = np.concatenate(parts); del raw
    src.append({'file': C6 + 'base_init.bin', 'lo': 25350000, 'hi': 61262999, 'rows': len(B), 'url': 'https://base.gateway.tenderly.co'})
    ext = load_json('raw/initext_8453.json.gz')
    E = np.zeros(len(ext), dtype=dt)
    for i, r in enumerate(ext):
        E[i] = (r[0], bytes.fromhex(r[1][2:]), bytes.fromhex(r[2][2:]), bytes.fromhex(r[3][2:]), bytes.fromhex(r[6][2:]), r[4].to_bytes(3, 'big'), (r[5] & 0xffffff).to_bytes(3, 'big'))
    A = np.concatenate([B, E]); del B
    ib = A['id'].tobytes(); seen = set(); keep = []
    for i in range(len(A)):
        k = ib[32 * i:32 * i + 32]
        if k not in seen: seen.add(k); keep.append(i)
    A = A[np.array(keep)]
    fee = np.array([int.from_bytes(x, 'big') for x in A['fee']], dtype=np.int64) if len(A) < 0 else None
else:
    if cid in (56, 196, 480): rows = load_json(C6 + 'init_%d.json.gz' % cid)
    else: rows = load_json(C5 + 'init_%d.json.gz' % cid)
    rows = [list(r) for r in rows] + load_json('raw/initext_%d.json.gz' % cid)
    seen = set(); R = []
    for r in rows:
        if r[1] in seen: continue
        seen.add(r[1]); R.append(r)
    dt = np.dtype([('b', '>u4'), ('id', 'V32'), ('c0', 'V20'), ('c1', 'V20'), ('h', 'V20'), ('fee', 'V3'), ('ts', 'V3')])
    A = np.zeros(len(R), dtype=dt)
    for i, r in enumerate(R):
        A[i] = (r[0], bytes.fromhex(r[1][2:]), bytes.fromhex(r[2][2:]), bytes.fromhex(r[3][2:]), bytes.fromhex(r[6][2:]), (r[4] & 0xffffff).to_bytes(3, 'big'), (r[5] & 0xffffff).to_bytes(3, 'big'))
print(cid, 'pools', len(A), flush=True)
# abi.encode(PoolKey) = c0 | c1 | uint24 fee | int24 tickSpacing (sign extended) | hooks, 160 bytes
n = len(A); M = np.zeros((n, 160), dtype=np.uint8)
M[:, 12:32] = np.frombuffer(A['c0'].tobytes(), dtype=np.uint8).reshape(n, 20)
M[:, 44:64] = np.frombuffer(A['c1'].tobytes(), dtype=np.uint8).reshape(n, 20)
M[:, 93:96] = np.frombuffer(A['fee'].tobytes(), dtype=np.uint8).reshape(n, 3)
ts = np.frombuffer(A['ts'].tobytes(), dtype=np.uint8).reshape(n, 3)
M[:, 125:128] = ts; neg = ts[:, 0] >= 0x80; M[neg, 96:125] = 0xff
M[:, 140:160] = np.frombuffer(A['h'].tobytes(), dtype=np.uint8).reshape(n, 20)
p = subprocess.run(['build/kec', '160'], input=M.tobytes(), capture_output=True); del M
H = np.frombuffer(p.stdout, dtype='V32')
mism = np.nonzero(np.any(np.frombuffer(p.stdout, dtype=np.uint8).reshape(n, 32) != np.frombuffer(A['id'].tobytes(), dtype=np.uint8).reshape(n, 32), axis=1))[0]
print(cid, 'recomputed', len(H), 'mismatch', len(mism), flush=True)
hb = A['h'].tobytes(); HK = [hb[20 * i:20 * i + 20] for i in range(n)]
hooks = collections.Counter(HK)
hl = [h for h in hooks if h != b'\0' * 20]
blk = hex(int(rpc(url, 'eth_blockNumber', []), 16) - 10); cv0 = rpc(url, 'web3_clientVersion', [])
CODE = '0x5f5b3681101560145780353b8152602001600156' + '5b365ff3'; HELP = '0x00000000000000000000000000000000c0de5122'
size = {}
for i in range(0, len(hl), PER):
    part = hl[i:i + PER]; data = '0x' + ''.join(h.hex().rjust(64, '0') for h in part)
    for k in range(8):
        try:
            r = rpc(url, 'eth_call', [{'to': HELP, 'data': data, 'gas': hex(30_000_000)}, blk, {HELP: {'code': CODE}}], tries=3); break
        except Exception as e:
            time.sleep(2 * (k + 1)); err = e
    else: raise err
    for j, h in enumerate(part): size[h] = int(r[2 + 64 * j:66 + 64 * j], 16)
    if i // PER % 20 == 0: print(cid, 'sizes', i + len(part), '/', len(hl), flush=True)
cv1 = rpc(url, 'web3_clientVersion', [])
emp = [h for h in hl if size[h] == 0]; d23 = [h for h in hl if size[h] == 23]
codes = {}
for h in d23: codes[h] = rpc(url, 'eth_getCode', ['0x' + h.hex(), blk])
deleg = [h for h in d23 if codes[h].lower().startswith('0xef0100')]
sel_e = set(emp); sel_d = set(deleg); sel = sel_e | sel_d
idx = [i for i in range(n) if HK[i] in sel]; HB = H.tobytes(); IB = A['id'].tobytes()
out = {'chainId': cid, 'url': url, 'block': int(blk, 16), 'clientVersionStart': cv0, 'clientVersionEnd': cv1, 'sources': src,
       'pools': int(len(A)), 'poolsWithHook': int(sum(v for h, v in hooks.items() if h != b'\0' * 20)), 'distinctHooks': len(hl),
       'idMismatch': [{'row': int(i), 'topic': '0x' + IB[32 * i:32 * i + 32].hex(), 'recomputed': '0x' + HB[32 * i:32 * i + 32].hex(), 'block': int(A['b'][i])} for i in mism],
       'emptyHooks': len(emp), 'delegatedHooks': len(deleg), 'size23NotDelegated': [('0x' + h.hex(), codes[h][:20]) for h in d23 if h not in deleg],
       'hookPools': [{'poolId': '0x' + HB[32 * i:32 * i + 32].hex(), 'topicId': '0x' + IB[32 * i:32 * i + 32].hex(), 'block': int(A['b'][i]), 'currency0': '0x' + A['c0'][i].tobytes().hex(), 'currency1': '0x' + A['c1'][i].tobytes().hex(),
                      'fee': int.from_bytes(A['fee'][i].tobytes(), 'big'), 'tickSpacing': int.from_bytes(A['ts'][i].tobytes(), 'big', signed=True), 'hook': '0x' + HK[i].hex(),
                      'kind': 'empty' if HK[i] in sel_e else 'delegated', 'delegate': ('0x' + codes[HK[i]][8:48]) if HK[i] in sel_d else None} for i in idx]}
json.dump(out, open('raw/census_%d.json' % cid, 'w'), indent=1)
print(cid, 'block', int(blk, 16), 'hooks', len(hl), 'empty', len(emp), 'delegated', len(deleg), 'pools on them', len(idx), 'mismatch', len(mism), flush=True)
