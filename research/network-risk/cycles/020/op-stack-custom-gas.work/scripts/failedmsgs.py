"""L-790: scan FailedRelayedMessage logs of the L2CrossDomainMessenger predeploy on Celo
(0x4200...0007) from the L2 migration block to head, then decode the relayMessage calldata
of each emitting transaction and look for messages whose final recipient is the PoolManager.
Read-only. Usage: python3 failedmsgs.py <out.json> [from] [to]"""
import sys, json, urllib.request, concurrent.futures as cf, time
URL = 'https://forno.celo.org'
MSGR = '0x4200000000000000000000000000000000000007'
T_FAIL = '0x99d0e048484baa1b1540b1367cb128acd7ab2946d1ed91ec10e3c85e4bf51b8f'
PM = '288dc841a52fca2707c6947b3a777c5e56cd87bc'
out = sys.argv[1]
def rpc(m, p):
    err = None
    for k in range(12):
        try:
            r = urllib.request.Request(URL, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            j = json.load(urllib.request.urlopen(r, timeout=90))
            if 'error' in j: raise RuntimeError(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + k)
    raise err
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 31056500
hi = int(sys.argv[3]) if len(sys.argv) > 3 else int(rpc('eth_blockNumber', []), 16)
step = 5000
ranges = [(a, min(a + step - 1, hi)) for a in range(lo, hi + 1, step)]
logs, fails = [], []
def get(r): return rpc('eth_getLogs', [{"address": MSGR, "topics": [T_FAIL], "fromBlock": hex(r[0]), "toBlock": hex(r[1])}])
with cf.ThreadPoolExecutor(8) as ex:
    futs = {ex.submit(get, r): r for r in ranges}
    for f in cf.as_completed(futs):
        try: logs += f.result()
        except Exception as e: fails.append([futs[f], str(e)[:200]])
# retry failed ranges once serially
still = []
for r, _ in fails:
    try: logs += get(r)
    except Exception as e: still.append([r, str(e)[:200]])
dec = []
for l in logs:
    tx = rpc('eth_getTransactionByHash', [l['transactionHash']])
    inp = tx['input'].lower()
    rec = {'block': int(l['blockNumber'], 16), 'tx': l['transactionHash'], 'msgHash': l['topics'][1], 'selector': inp[:10],
           'mentionsPoolManager': PM in inp, 'txTo': tx.get('to')}
    dec.append(rec)
hits = [d for d in dec if d['mentionsPoolManager']]
json.dump({'url': URL, 'from': lo, 'to': hi, 'ranges': len(ranges), 'unrecovered': still, 'failedRelays': len(logs), 'withPoolManager': hits, 'all': dec}, open(out, 'w'), indent=1)
print('ranges', len(ranges), 'failed relays', len(logs), 'unrecovered ranges', len(still), 'mentioning PoolManager', len(hits))
