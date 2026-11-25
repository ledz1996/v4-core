"""Read-only. ERC-4337 bundles among PoolManager transactions: for each chain, PoolManager log tx hashes in a
recent window, receipts, UserOperationEvent logs of the EntryPoint versions 0.6, 0.7 and 0.8, and for bundles with
two or more operations of distinct senders, the call tree: which operations' frames reached the PoolManager.
Usage: python3 aa.py <chainId> <logsUrl> <traceUrl> <maxTx> <step> <out.json>"""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
from evm import keccak
import scan as S
UOE = '0x' + keccak(b'UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)').hex()
EPS = {'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789', '0x0000000071727de22e5e9d8baf0edac6f37da032', '0x4337084d9e255ff0702461cf8895ce9e3b5ff108'}
cid, lurl, turl, mx, step, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
pm = nets[cid]['poolManager'].lower()
head = int(S.R(lurl, 'eth_blockNumber', []), 16)
hs, low = S.logs_window(lurl, pm, mx, head, step)
def rc(h):
    try: return h, S.R(lurl, 'eth_getTransactionReceipt', [h])
    except Exception as e: return h, None
with cf.ThreadPoolExecutor(4) as ex: recs = list(ex.map(rc, hs))
bund = []
for h, r in recs:
    if not r: continue
    ev = [l for l in r['logs'] if l['address'].lower() in EPS and l['topics'] and l['topics'][0].lower() == UOE]
    if ev:
        snd = ['0x' + l['topics'][2][-40:] for l in ev]
        bund.append({'tx': h, 'block': int(r['blockNumber'], 16), 'entryPoint': ev[0]['address'].lower(), 'ops': len(ev), 'senders': snd})
multi = [b for b in bund if len(set(b['senders'])) >= 2]
def walk(n, sender, acc):
    # innerHandleOp frames are EntryPoint self calls; the account call below names the sender
    to = (n.get('to') or '').lower(); fr = (n.get('from') or '').lower()
    if fr in EPS and to not in EPS and to != pm: sender = to
    if to == pm: acc.setdefault(sender, []).append((S.SEL.get(n.get('input', '')[2:10], n.get('input', '')[2:10]), 'error' not in n))
    for c in n.get('calls', []) or []: walk(c, sender, acc)
for b in multi[:12]:
    try:
        t = S.R(turl, 'debug_traceTransaction', [b['tx'], {'tracer': 'callTracer'}]); acc = {}; walk(t, None, acc)
        b['pmBySender'] = {k or 'none': v for k, v in acc.items()}
        b['sendersReachingPm'] = sorted(k for k in acc if k and k in set(b['senders']))
    except Exception as e: b['traceErr'] = str(e)[:120]
res = {'chain': cid, 'blocks': [low + 1, head], 'pmTxs': len(hs), 'bundles': len(bund), 'multiSenderBundles': len(multi),
       'sharedPm': [b for b in multi if len(b.get('sendersReachingPm', [])) >= 2], 'multi': multi[:12]}
json.dump(res, open(out, 'w'), indent=1)
print(cid, 'pmTxs', len(hs), 'bundles', len(bund), 'multiSender', len(multi), 'sharedPm', [(b['tx'], b['sendersReachingPm']) for b in res['sharedPm']][:3])
