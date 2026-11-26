"""Candidate selection: every log emitted by the PoolManager and every ERC-20 Transfer whose from or to
topic is the PoolManager, read with eth_getLogs over [lo, hi] newest first in chunks of `step` blocks
(halved on refusal). Stops when `maxtx` distinct transactions are collected; the covered range is recorded.
Usage: lister.py <chainId> <pm> <lo> <hi> <step> <maxtx> <out.json> <url> [<url>...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call
cid, pm, lo, hi, step, maxtx, out = sys.argv[1], sys.argv[2].lower(), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
URLS = sys.argv[8:]
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
PMT = '0x' + '0' * 24 + pm[2:]
state = {'chainId': int(cid), 'pm': pm, 'lo': lo, 'hi': hi, 'step': step, 'urls': URLS, 'refusals': [], 'chunks': [], 'logs': {}}
if os.path.exists(out):
    state = json.load(open(out))
state['clientVersionStart'] = {u: call(u, 'web3_clientVersion', []) for u in URLS}
k = 0


def getlogs(f, t, flt):
    global k
    last = None
    for a in range(len(URLS) * 3):
        u = URLS[(k + a) % len(URLS)]
        q = dict(flt); q['fromBlock'] = hex(f); q['toBlock'] = hex(t)
        res, err = call(u, 'eth_getLogs', [q], timeout=120)
        if err is None and res is not None:
            k += 1
            return res, u
        last = (u, err)
        state['refusals'].append({'url': u, 'range': [f, t], 'err': (err or 'null result')[:200]})
        el = (err or '').lower()
        if 'rate' in el or '429' in el or 'timed out' in el:
            time.sleep(5 + 5 * a); continue
        if 'range' in el or 'too many' in el or 'exceed' in el or '10000' in el or 'max' in el or 'block' in el:
            return None, last
        time.sleep(1 + a)
    return None, last


cur = state.get('cursor', hi)
s = step
logs = state['logs']
while cur >= lo and len({l['tx'] for l in logs.values()}) < maxtx:
    f = max(lo, cur - s + 1)
    ok = True; got = []
    for flt in ({'address': pm}, {'topics': [T, None, PMT]}, {'topics': [T, PMT]}):
        r, u = getlogs(f, cur, flt)
        if r is None:
            ok = False; break
        got.append((r, u))
    if not ok:
        if s > 1:
            s = max(1, s // 2); continue
        json.dump(state, open(out, 'w'))
        raise SystemExit('cannot read block %d' % cur)
    for r, u in got:
        for l in r:
            key = l['transactionHash'] + ':' + l['logIndex']
            logs[key] = {'tx': l['transactionHash'], 'block': int(l['blockNumber'], 16), 'txi': int(l['transactionIndex'], 16),
                         'addr': l['address'].lower(), 'topics': l['topics'], 'data': l['data'], 'li': int(l['logIndex'], 16)}
    state['chunks'].append([f, cur, sum(len(r) for r, _ in got), got[0][1]])
    cur = f - 1
    state['cursor'] = cur
    if ok and s < step and len(state['chunks']) % 20 == 0:
        s = min(step, s * 2)
    if len(state['chunks']) % 50 == 0:
        json.dump(state, open(out, 'w')); print(cid, 'cursor', cur, 'txs', len({l['tx'] for l in logs.values()}), flush=True)
state['coveredLo'] = cur + 1
state['clientVersionEnd'] = {u: call(u, 'web3_clientVersion', []) for u in URLS}
json.dump(state, open(out, 'w'))
print(cid, 'done covered', state['coveredLo'], hi, 'txs', len({l['tx'] for l in logs.values()}), 'logs', len(logs))
