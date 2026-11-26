"""Read-only queries for Task 3, bracketed with web3_clientVersion. usage: chainq.py <step>  (results appended to ../out/chainq.jsonl)"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from replaycov import NETS
from pyevm_cov import keccak
OUT = '../out/chainq.jsonl'
def rec(**k):
    k['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()); open(OUT, 'a').write(json.dumps(k) + '\n'); return k
def topic(s): return '0x' + keccak(s.encode()).hex()
SWAP = topic('Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)'); DON = topic('Donate(bytes32,address,uint256,uint256)')
INIT = topic('Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)')
EPS = {143: 'https://rpc.monad.xyz', 4326: 'https://mainnet.megaeth.com/rpc', 999: 'https://rpc.hyperliquid.xyz/evm'}
step = sys.argv[1]
if step == 'pfc':
    for c, u in EPS.items():
        a = call(u, 'web3_clientVersion', [], 30); h = call(u, 'eth_blockNumber', [], 30)[0]
        s2 = call(u, 'eth_getStorageAt', [NETS[c]['poolManager'], '0x2', 'latest'], 30); s0 = call(u, 'eth_getStorageAt', [NETS[c]['poolManager'], '0x0', 'latest'], 30)
        b = call(u, 'web3_clientVersion', [], 30)
        print(rec(step='pfc', chainId=c, url=u, clientBefore=a, clientAfter=b, head=h, slot2_protocolFeeController=s2, slot0_owner=s0))
if step == 'span':
    c = int(sys.argv[2]); u = sys.argv[3] if len(sys.argv) > 3 else EPS[c]; span = int(sys.argv[4]) if len(sys.argv) > 4 else 100000
    a = call(u, 'web3_clientVersion', [], 30); h = int(call(u, 'eth_blockNumber', [], 30)[0], 16)
    r, e = call(u, 'eth_getLogs', [{'address': NETS[c]['poolManager'], 'topics': [DON], 'fromBlock': hex(h - span), 'toBlock': hex(h)}], 90)
    b = call(u, 'web3_clientVersion', [], 30)
    print(rec(step='span', chainId=c, url=u, clientBefore=a, clientAfter=b, head=h, span=span, n=None if r is None else len(r), err=e))
if step == 'scan':
    # scan PoolManager logs of the given topics in [lo, hi] with a fixed span; writes ../out/logs-<cid>-<tag>.json
    c = int(sys.argv[2]); u = sys.argv[3]; lo = int(sys.argv[4]); hi = int(sys.argv[5]); span = int(sys.argv[6]); tag = sys.argv[7]
    T6909 = topic('Transfer(address,address,address,uint256,uint256)'); APPR = topic('Approval(address,address,uint256,uint256)'); OPS = topic('OperatorSet(address,address,bool)')
    tops = {'donate': [DON], 'swap': [SWAP], 'init': [INIT], 'all': None, 'erc6909': [[T6909, APPR, OPS]]}[tag]
    a = call(u, 'web3_clientVersion', [], 30); out = []; errs = []; b0 = lo
    while b0 <= hi:
        b1 = min(hi, b0 + span - 1); q = {'address': NETS[c]['poolManager'], 'fromBlock': hex(b0), 'toBlock': hex(b1)}
        if tops: q['topics'] = tops
        for t in range(8):
            r, e = call(u, 'eth_getLogs', [q], 120)
            if e is None: break
            errs.append([b0, b1, e[:120]]); time.sleep(2 + 2 * t)
        if r is None: break
        out += r; b0 = b1 + 1
    b = call(u, 'web3_clientVersion', [], 30)
    json.dump({'chainId': c, 'url': u, 'range': [lo, hi], 'reachedTo': b0 - 1, 'tag': tag, 'clientBefore': a, 'clientAfter': b, 'errors': errs[:50], 'nErrors': len(errs), 'logs': out}, open('../out/logs-%d-%s-%d.json' % (c, tag, lo), 'w'))
    print(rec(step='scan', chainId=c, url=u, range=[lo, hi], reachedTo=b0 - 1, tag=tag, n=len(out), nErrors=len(errs), clientBefore=a, clientAfter=b))
