# Follow-up for every implementation or embedded address X that answered balanceOf(PoolManager) with a nonzero figure:
# compare with the pooled token T that names X, and test whether a transfer of one by the PoolManager address moves the other.
import sys, os, json, gzip
T6 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '006', 'theme-currency-lists.work')
sys.path.insert(0, T6)
from common import *
from mirror import MIRROR, SINK
from lib import sel
HERE2 = os.path.dirname(os.path.abspath(__file__))
def s(cid, to, sig, *args):
    r = ecall(cid, to, '0x' + sel(sig).replace('0x', '') + ''.join(adr(a) if isinstance(a, str) else u256(a) for a in args))
    return r
def text(r):
    if not isinstance(r, str) or len(r) < 130: return r if not isinstance(r, str) else r[:20]
    try:
        n = int(r[66:130], 16); return bytes.fromhex(r[130:130 + 2 * n]).decode('utf8', 'replace')
    except Exception: return r[:40]
def run(cid):
    pm = net(cid)['poolManager']
    d = json.load(open(os.path.join(HERE2, 'raw', 'impl_face_%d.json' % cid)))
    out = []
    for X, info in d['nonzero'].items():
        for T in info['proxies']:
            row = {'X': X, 'T': T}
            row['X.balanceOf'] = s(cid, X, 'balanceOf(address)', pm); row['T.balanceOf'] = s(cid, T, 'balanceOf(address)', pm)
            row['X.symbol'] = text(s(cid, X, 'symbol()')); row['T.symbol'] = text(s(cid, T, 'symbol()'))
            row['X.decimals'] = s(cid, X, 'decimals()'); row['T.decimals'] = s(cid, T, 'decimals()')
            cl = rpc(urls2(cid)[0], 'eth_getCode', [X, 'latest']); cl = cl if isinstance(cl, str) else (cl.get('result') or '0x'); row['X.codeLen'] = len(cl) // 2 - 1
            # the PoolManager address sends one third of its T balance: does X.balanceOf(PoolManager) move? and the reverse
            for a, o, k in ((T, X, 'send T, read X'), (X, T, 'send X, read T')):
                r = ecall(cid, pm, '0x' + adr(SINK) + adr(a) + adr(o), {pm: {'code': MIRROR}}, gas=20_000_000)
                row[k] = [int(r[2:66], 16), int(r[66:130], 16)] if isinstance(r, str) and len(r) == 130 else r
            out.append(row); print(cid, json.dumps({k: (v if not isinstance(v, dict) else 'ERR ' + json.dumps(v)[:90]) for k, v in row.items()}), flush=True)
    json.dump(out, open(os.path.join(HERE2, 'raw', 'impl_follow_%d.json' % cid), 'w'), indent=1)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
