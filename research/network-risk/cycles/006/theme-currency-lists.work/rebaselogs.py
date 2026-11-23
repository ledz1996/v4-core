# All logs of one topic emitted by one contract over a block range (address filtered eth_getLogs). Used for the rebase logs of sSAC.
# usage: python3 rebaselogs.py <chainId> <url> <chunk> <fromBlock> <address> <topic0> <tag>
import sys, json, gzip, threading
from lib import *
from fetch import getlogs_range
cid = int(sys.argv[1]); url = sys.argv[2]; chunk = int(sys.argv[3]); lo = int(sys.argv[4]); addr = sys.argv[5]; topic = sys.argv[6]; tag = sys.argv[7]
head = int(rpc(url, 'eth_blockNumber', []), 16) - 10; rows = []; lock = threading.Lock()
def on(logs):
    with lock:
        for l in logs: rows.append([int(l['blockNumber'], 16), l['transactionHash'], l['topics'], l['data']])
st = getlogs_range(url, {'address': addr, 'topics': [topic]}, lo, head, chunk, workers=4, on_logs=on, label=tag)
rows.sort(); json.dump(dict(chainId=cid, address=addr, topic=topic, lo=lo, hi=head, fail=st['fail'], rows=rows), gzip.open('raw/logs_%d_%s.json.gz' % (cid, tag), 'wt'))
print(cid, tag, 'rows', len(rows), 'fail', len(st['fail']), flush=True)
