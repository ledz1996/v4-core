"""Cycle 22 driver for the cycle 6 transfer census rule. It imports census2.segment from
cycles/006/theme-currency-lists.work unchanged and only replaces (a) the endpoints, (b) the pool map, which is the
cycle 5/6 Initialize list plus Initialize logs fetched here from the list's last block to the range end, and
(c) the block range, which is given explicitly instead of as days back from head.
Read-only: eth_getLogs, eth_blockNumber, web3_clientVersion.
usage: census3.py <chainId> <B1> <B2> <segBlocks> <tag> <logUrl> <chunk> <workers>"""
import sys, os, json, gzip, struct, time
HERE = os.path.dirname(os.path.abspath(__file__))
C6 = os.path.join(HERE, '..', '..', '006', 'theme-currency-lists.work'); C5 = os.path.join(HERE, '..', '..', '005', 'theme-shared-hooks.work')
sys.path.insert(0, C6)
import census2
from lib import rpc
from fetch import getlogs_range
cid, B1, B2, SEG, tag, URL, CHUNK, W = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6], int(sys.argv[7]), int(sys.argv[8])
census2.CFG[cid] = dict(census2.CFG[cid]); census2.CFG[cid]['logs'] = URL; census2.CFG[cid]['chunk'] = CHUNK; census2.CFG[cid]['workers'] = W
census2.LOGSRC.pop(cid, None); census2.PMLOGS[cid] = (URL, CHUNK)
pm = census2.net(cid)['poolManager']
INITX = os.path.join(HERE, 'raw', 'initx_%d.json' % cid)
def base_list():
    for fn in [os.path.join(C6, 'raw', 'init_%d.json.gz' % cid), os.path.join(C5, 'raw', 'init_%d.json.gz' % cid)]:
        if os.path.exists(fn):
            d = json.load(gzip.open(fn)); return {r[1]: (r[2][2:], r[3][2:]) for r in d['rows']}, d['hi'], fn
    return {}, None, None
if cid == 8453: BASE, HI, SRC = None, 61263987, os.path.join(C6, 'raw', 'base_init.bin')  # base_init.py windows of 1000 from 25350988, 35913 windows: last block 61263987
else: BASE, HI, SRC = base_list()
# Initialize logs after the list's end, up to B2
ext = json.load(open(INITX)) if os.path.exists(INITX) else {'from': None, 'to': None, 'rows': {}}
lo = (HI + 1) if HI is not None else B1
if B2 >= lo and (ext['to'] is None or ext['to'] < B2):
    a = lo if ext['to'] is None else ext['to'] + 1
    rows = ext['rows']
    def on(logs):
        for l in logs:
            if not l.get('removed') and l['topics'][0] == census2.INIT: rows[l['topics'][1]] = [l['topics'][2][-40:], l['topics'][3][-40:]]
    st = getlogs_range(URL, {'address': pm, 'topics': [census2.INIT]}, a, B2, int(os.environ.get('INITCHUNK', CHUNK * 10)), workers=W, on_logs=on, label='%d init' % cid)
    ext = {'from': ext['from'] or a, 'to': B2, 'rows': rows, 'url': URL, 'fail': st['fail'][:20], 'nFail': len(st['fail'])}
    json.dump(ext, open(INITX, 'w'))
    print(cid, 'initx', a, B2, 'new pools', len(rows), 'fails', len(st['fail']), flush=True)
def pool_map(c, ids):
    m = {}
    if cid == 8453:
        want = {bytes.fromhex(i[2:]) for i in ids}
        with open(SRC, 'rb') as f:
            while True:
                h = f.read(8)
                if len(h) < 8: break
                a, n = struct.unpack('>II', h); body = f.read(102 * n)
                for k in range(n):
                    r = body[102 * k: 102 * k + 102]
                    if r[4:36] in want: m['0x' + r[4:36].hex()] = (r[36:56].hex(), r[56:76].hex())
    else:
        for i in ids:
            if i in BASE: m[i] = BASE[i]
    for i in ids:
        if i in ext['rows']: m[i] = tuple(ext['rows'][i])
    return m
census2.pool_map = pool_map
out = os.path.join(HERE, 'raw', 'census3_%d_%s.json.gz' % (cid, tag))
cv0 = rpc(URL, 'web3_clientVersion', []); t0 = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
import collections
C = collections.Counter(); flagged = []; agg = dict(txs=0, pooltx=0, unk=0, fails=collections.Counter(), req=0, logs=0, segs=[])
a = B1
while a <= B2:
    b = min(a + SEG - 1, B2); o = census2.segment(cid, a, b)
    C.update(o['counts']); flagged += o['flagged']; agg['txs'] += o['txs']; agg['pooltx'] += o['txsWithPoolEvent']; agg['unk'] += o['poolsUnknown']
    sf = {}
    for k, v in o['stats'].items(): agg['fails'][k] += v['nFail']; agg['req'] += v['req']; agg['logs'] += v['logs']; sf[k] = [v['logs'], v['nFail'], v['fail']]
    agg['segs'].append([a, b, o['txs'], sf])
    print(cid, tag, 'segment', a, b, 'txs', o['txs'], 'flagged', len(flagged), dict(o['counts']), time.strftime('%H:%M:%S'), flush=True)
    json.dump(dict(chainId=cid, url=URL, clientVersionStart=[t0, cv0], B1=B1, B2=b, wantB2=B2, partial=b < B2, counts=dict(C), flagged=flagged, fails=dict(agg['fails']),
                   req=agg['req'], logs=agg['logs'], txs=agg['txs'], txsWithPoolEvent=agg['pooltx'], poolsUnknown=agg['unk'], segments=agg['segs'], initList=SRC, initListHi=HI,
                   initExt=[ext['from'], ext['to'], len(ext['rows'])]), gzip.open(out, 'wt'))
    a = b + 1
cv1 = rpc(URL, 'web3_clientVersion', [])
d = json.load(gzip.open(out)); d['clientVersionEnd'] = [time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), cv1]; json.dump(d, gzip.open(out, 'wt'))
print(cid, tag, 'DONE', dict(C), 'txs', agg['txs'], 'fails', dict(agg['fails']), flush=True)
