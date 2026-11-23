# Full Initialize history of the Base PoolManager through base.gateway.tenderly.co in windows of 1,000 blocks.
# Read-only: eth_getLogs. Resumable: raw/base_init.bin holds records [u32 windowStart][u32 count] + count rows of 102 bytes
# (u32 block, 32 poolId, 20 currency0, 20 currency1, 20 hooks, u24 fee, i24 tickSpacing). raw/base_init.fail lists refused windows.
# usage: python3 base_init.py <fromBlock> <toBlock> <workers>
import sys, os, json, struct, threading, time, concurrent.futures as cf
from lib import *
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
URL = 'https://base.gateway.tenderly.co'
pm = net(8453)['poolManager']; lo = int(sys.argv[1]); hi = int(sys.argv[2]); W = int(sys.argv[3])
FN = 'raw/base_init.bin'; done = set()
if os.path.exists(FN):
    with open(FN, 'rb') as f:
        while True:
            h = f.read(8)
            if len(h) < 8: break
            a, n = struct.unpack('>II', h); body = f.read(102 * n)
            if len(body) < 102 * n: break
            done.add(a)
            good = f.tell()
    os.truncate(FN, good if done else 0)
out = open(FN, 'ab'); lock = threading.Lock(); st = {'w': 0, 'logs': 0, 'fail': 0}
wins = [a for a in range(lo, hi + 1, 1000) if a not in done]
print('windows todo', len(wins), 'done before', len(done), flush=True)
def get(a, b):
    for k in range(8):
        try:
            j = post(URL, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [INIT], 'fromBlock': hex(a), 'toBlock': hex(b)}]}, timeout=90, tries=3)
        except Exception as e:
            time.sleep(2 + 2 * k); continue
        if 'error' in j:
            m = json.dumps(j['error']).lower()
            if 'range' in m or 'too large' in m or 'exceed' in m or 'size' in m:
                if b > a:
                    mid = (a + b) // 2; x = get(a, mid); y = get(mid + 1, b)
                    return None if x is None or y is None else x + y
            time.sleep(2 + 2 * k); continue
        return j['result']
    return None
def one(a):
    b = min(a + 999, hi); r = get(a, b)
    with lock:
        if r is None:
            st['fail'] += 1; open('raw/base_init.fail', 'a').write('%d\n' % a); return
        buf = bytearray(struct.pack('>II', a, len(r)))
        for l in r:
            d = l['data'][2:]; t = l['topics']
            fee = int(d[0:64], 16) & 0xffffff; ts = int(d[64:128], 16) & 0xffffff
            buf += struct.pack('>I', int(l['blockNumber'], 16)) + bytes.fromhex(t[1][2:]) + bytes.fromhex(t[2][-40:]) + bytes.fromhex(t[3][-40:]) + bytes.fromhex(d[128:192][-40:]) + fee.to_bytes(3, 'big') + ts.to_bytes(3, 'big')
        out.write(buf); st['w'] += 1; st['logs'] += len(r)
        if st['w'] % 500 == 0: out.flush(); print('windows', st['w'], '/', len(wins), 'logs', st['logs'], 'fail', st['fail'], time.strftime('%H:%M:%S'), flush=True)
with cf.ThreadPoolExecutor(W) as ex: list(ex.map(one, wins))
out.close(); print('finished', st, flush=True)
