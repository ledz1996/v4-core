"""Recount two earlier log counts that came from publicnode on tenderly, which passes gapcheck2 (drpc dropped after a first try timed out at 600 s). Read-only eth_getLogs.
F-104: Donate logs of the Ethereum PoolManager, blocks 26,474,597 to 26,479,597 (108 on publicnode).
F-072: VCNT Transfer logs touching the Polygon PoolManager, blocks 97,364,523 to 97,804,523 (15 on publicnode, 9 out and 6 in)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'theme-currency-lists.work'))
from lib import rpc, pad_addr, TRANSFER
from fetch import getlogs_range
out = {}
DON = '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb'
for u in ([] if os.environ.get('ONLY137') else ['https://mainnet.gateway.tenderly.co']):
    L = []
    try: cv = rpc(u, 'web3_clientVersion', [])
    except Exception as e: cv = str(e)[:100]
    st = getlogs_range(u, {'address': '0x000000000004444c5dc75cB358380D2e3dE08A90', 'topics': [DON]}, 26474597, 26479597, 1000, workers=1, on_logs=L.extend)
    out['F-104 ' + u] = dict(clientVersion=cv, logs=len(L), fail=st['fail'])
pm = pad_addr('0x67366782805870060151383f4bbff9dab53e5cd6'); V = '0x8a16d4bf8a0a716017e8d2262c4ac32927797a2f'  # VCNT token (F-072 difference field)
for u in ['https://polygon.gateway.tenderly.co']:
    o, i = [], []
    try: cv = rpc(u, 'web3_clientVersion', [])
    except Exception as e: cv = str(e)[:100]
    s1 = getlogs_range(u, {'address': V, 'topics': [TRANSFER, pm]}, 97364523, 97804523, 10000, workers=2, on_logs=o.extend)
    s2 = getlogs_range(u, {'address': V, 'topics': [TRANSFER, None, pm]}, 97364523, 97804523, 10000, workers=2, on_logs=i.extend)
    out['F-072 ' + u] = dict(clientVersion=cv, out=len(o), inn=len(i), fail=s1['fail'] + s2['fail'])
old = json.load(open('raw/xcheck.json')) if os.path.exists('raw/xcheck.json') else {}; old.update(out); out = old
json.dump(out, open('raw/xcheck.json', 'w'), indent=1); print(json.dumps(out, indent=1))
