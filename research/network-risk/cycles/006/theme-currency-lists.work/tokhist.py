# Whole history of Transfer logs between one token and the PoolManager (address filtered eth_getLogs), read-only.
# usage: python3 tokhist.py <chainId> <url> <chunk> <fromBlock> <token> [token ...]   -> raw/tokhist_<cid>_<token8>.json.gz
import sys, json, gzip, threading
from lib import *
from fetch import getlogs_range
cid = int(sys.argv[1]); url = sys.argv[2]; chunk = int(sys.argv[3]); lo = int(sys.argv[4]); pm = net(cid)['poolManager'].lower(); p = pad_addr(pm)
head = int(rpc(url, 'eth_blockNumber', []), 16) - 10
for tok in sys.argv[5:]:
    rows = []; lock = threading.Lock()
    def on(logs):
        with lock:
            for l in logs:
                if l.get('removed') or len(l['topics']) != 3: continue
                rows.append([int(l['blockNumber'], 16), l['transactionHash'], int(l['logIndex'], 16), '0x' + l['topics'][1][-40:], '0x' + l['topics'][2][-40:], str(int(l['data'], 16)) if len(l['data']) > 2 else '0'])
    s1 = getlogs_range(url, {'address': tok, 'topics': [TRANSFER, p]}, lo, head, chunk, workers=4, on_logs=on, label='out')
    s2 = getlogs_range(url, {'address': tok, 'topics': [TRANSFER, None, p]}, lo, head, chunk, workers=4, on_logs=on, label='in')
    rows.sort()
    json.dump(dict(chainId=cid, token=tok, lo=lo, hi=head, url=url, fail=s1['fail'] + s2['fail'], rows=rows), gzip.open('raw/tokhist_%d_%s.json.gz' % (cid, tok[2:10]), 'wt'))
    print(cid, tok, 'rows', len(rows), 'out', sum(1 for r in rows if r[3] == pm), 'in', sum(1 for r in rows if r[4] == pm), 'fail', len(s1['fail']) + len(s2['fail']), flush=True)
