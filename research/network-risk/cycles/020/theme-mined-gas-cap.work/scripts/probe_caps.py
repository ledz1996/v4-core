"""Read-only probe of per-transaction gas limits on each network.
usage: python3 -I probe_caps.py <out.json> [chainId ...]
For each chain: client version, head gasLimit, largest gas limit among txs mined in the last K blocks,
whether eth_call accepts given gas values, and what eth_estimateGas returns for a probe contract
(injected by state override at an unused address) that succeeds only when at least X gas is left."""
import sys, json, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/020/theme-mined-gas-cap.work/scripts')
from rpc import call, NET

PROBE = '0x00000000000000000000000000000000000ca9e1'
def needgas(x):
    # PUSH4 x GAS LT PUSH1 0x0b JUMPI STOP JUMPDEST PUSH1 0 DUP1 REVERT
    return '0x63' + format(x, '08x') + '5a10600b57005b600080fd'

def probe(n, K):
    url = n['rpc']; r = {'chainId': n['chainId'], 'name': n['name'], 'rpc': url}
    r['clientVersion'] = call(url, 'web3_clientVersion', []).get('result')
    head = call(url, 'eth_getBlockByNumber', ['latest', False]).get('result') or {}
    hn = int(head.get('number', '0x0'), 16)
    r['head'] = hn; r['headGasLimit'] = int(head.get('gasLimit', '0x0'), 16)
    mx = 0; mxh = None; over24 = 0; over30 = 0; ntx = 0; blocks = 0
    for b in range(hn, hn - K, -1):
        blk = call(url, 'eth_getBlockByNumber', [hex(b), True]).get('result')
        if not blk: continue
        blocks += 1
        for tx in blk.get('transactions', []):
            if not isinstance(tx, dict): continue
            g = int(tx.get('gas', '0x0'), 16); ntx += 1
            if tx.get('type') == '0x7e':
                continue  # OP deposits are exempt; count separately
            if g > mx: mx = g; mxh = tx.get('hash')
            if g > 2**24: over24 += 1
            if g > 30_000_000: over30 += 1
    r['scan'] = {'blocks': blocks, 'from': hn - K + 1, 'to': hn, 'txs': ntx, 'maxGasNonDeposit': mx, 'maxTx': mxh,
                 'over2p24': over24, 'over30M': over30}
    calls = {}
    for g in [2**24, 2**24 + 1, 30_000_000, 30_000_001, 2**25 + 1, 60_000_000]:
        res = call(url, 'eth_call', [{'to': '0x000000000000000000000000000000000000dEaD', 'gas': hex(g)}, 'latest'])
        calls[str(g)] = res.get('result', res.get('error', res))
    r['ethCall'] = calls
    est = {}
    for x in [10_000_000, 20_000_000, 31_000_000, 40_000_000]:
        res = call(url, 'eth_estimateGas', [{'to': PROBE, 'data': '0x'}, 'latest', {PROBE: {'code': needgas(x)}}])
        v = res.get('result')
        est[str(x)] = int(v, 16) if isinstance(v, str) else res.get('error', res)
    r['estimateNeedGas'] = est
    return r

if __name__ == '__main__':
    out = sys.argv[1]
    ids = [int(a) for a in sys.argv[2:]] or [n['chainId'] for n in NET]
    nets = [n for n in NET if n['chainId'] in ids]
    K = 12
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda n: probe(n, K), nets))
    json.dump(res, open(out, 'w'), indent=1)
    for r in res:
        print(r['chainId'], r['name'], r['clientVersion'], r['headGasLimit'], r['scan']['maxGasNonDeposit'], r['scan']['over2p24'],
              {k: (v if not isinstance(v, dict) else v.get('message', v))[:60] if isinstance(v, (str, dict)) else v for k, v in r['ethCall'].items()},
              r['estimateNeedGas'])
