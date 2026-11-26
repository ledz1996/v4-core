# Copied from cycles/023/theme-hyperevm-twin-state.work/scripts/replica_read.py
# Phase B: read the same items on a replica at the block number the official endpoint reported for each batch,
# then re-read any mismatch at the neighbouring blocks to separate a real difference from a write in between.
import json, sys, time
from rpc import rpc, batch
R = sys.argv[1]; out = sys.argv[2]
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
d = json.load(open('../raw/official_reads.json'))
def call(kind, x, b):
    if kind == 'slot': return ('eth_getStorageAt', [PM, x, hex(b)])
    if kind == 'native': return ('eth_getBalance', [PM, hex(b)])
    return ('eth_call', [{'to': x, 'data': '0x70a08231' + PM[2:].lower().rjust(64, '0')}, hex(b)])
def norm(v):
    try: return int(v, 16) if isinstance(v, str) and v.startswith('0x') else v
    except Exception: return v
res = {'replica': R, 'clientVersionStart': rpc(R, 'web3_clientVersion', []), 'compared': 0, 'equal': 0, 'mismatch': [], 'errors': []}
reads = d['reads']
for i in range(0, len(reads), 20):
    ch = reads[i:i + 20]
    for k in range(6):
        try: rr = batch(R, [call(r[0], r[1], r[3]) for r in ch], timeout=120); break
        except Exception as e: res['errors'].append([i, str(e)[:150]]); time.sleep(5 * (k + 1)); rr = None
    if rr is None: continue
    for r, v in zip(ch, rr):
        res['compared'] += 1
        if norm(v) == norm(r[2]): res['equal'] += 1
        else: res['mismatch'].append({'kind': r[0], 'key': r[1], 'official': r[2], 'officialBlock': r[3], 'replicaAtBlock': v})
    if (i // 20) % 50 == 0: print(i, res['compared'], len(res['mismatch']), flush=True)
for m in res['mismatch']:
    m['neighbours'] = {}
    for b in range(m['officialBlock'] - 3, m['officialBlock'] + 4):
        try: m['neighbours'][b] = batch(R, [call(m['kind'], m['key'], b)])[0]
        except Exception as e: m['neighbours'][b] = 'ERR ' + str(e)[:100]
    m['matchesNeighbour'] = any(norm(v) == norm(m['official']) for v in m['neighbours'].values())
res['clientVersionEnd'] = rpc(R, 'web3_clientVersion', [])
json.dump(res, open(out, 'w'), indent=0)
print('done', res['compared'], res['equal'], len(res['mismatch']), sum(1 for m in res['mismatch'] if not m['matchesNeighbour']))
