"""L-774 second step: receipts of sampled blocks against eth_getLogs counts, and a recent window on reth-bsc."""
import json, sys, random, urllib.request, time
PM = '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
def rpc(url, m, p):
    for a in range(4):
        try:
            r = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            j = json.loads(urllib.request.urlopen(r, timeout=60).read())
            if 'error' in j: raise Exception(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + a)
    raise err
d = json.load(open('l774_logs.json'))
per = {int(k): v for k, v in d['48club']['per'].items()}
rnd = random.Random(774)
blocks = sorted(rnd.sample(range(135480000, 135490000), 40))
out = {'sample': []}
for b in blocks:
    rc = rpc('https://bsc-dataseed1.bnbchain.org', 'eth_getBlockReceipts', [hex(b)])
    n = sum(1 for r in rc for l in r['logs'] if l['address'].lower() == PM)
    pn = len(rpc('https://bsc-rpc.publicnode.com', 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}]))
    try:
        ds = len(rpc('https://bsc-dataseed1.bnbchain.org', 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(b)}]))
    except Exception as e:
        ds = 'refused: ' + str(e)[:60]
    out['sample'].append({'block': b, 'receiptsDataseed1': n, 'logs48club': per.get(b, 0), 'logsPublicnodeSingle': pn, 'logsDataseed1Single': ds})
    print(out['sample'][-1], flush=True)
head = int(rpc('https://bsc-rpc.publicnode.com', 'eth_blockNumber', []), 16)
rec = {}
for name, url in [('publicnode-reth', 'https://bsc-rpc.publicnode.com'), ('48club', 'https://rpc-bsc.48.club')]:
    rec[name] = len(rpc(url, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(head - 300), 'toBlock': hex(head - 200)}]))
out['recent'] = {'from': head - 300, 'to': head - 200, 'counts': rec}
print(out['recent'])
json.dump(out, open('l774_receipts.json', 'w'), indent=0)
