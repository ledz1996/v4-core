"""Mined evidence by logs (read-only eth_getLogs): Donate and Swap events of the deployed PoolManager from <from> to head.
Adaptive block range (halves on error). Records counts, the Donate logs in full and, for Swap, the count and the largest
log2(liquidity * sqrtPriceX96) seen. Usage: python3 logs39.py <label> <url> <pm> <from> <range> <out.json>"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc as _rpc, keccak
def rpc(url, m, p, timeout=60):
    last = None
    for k in range(8):
        try: return _rpc(url, m, p, timeout=timeout)
        except Exception as e:
            last = e
            if '429' not in str(e) and 'rate limit' not in str(e): raise
            time.sleep(5 * (k + 1))
    raise last
label, url, pm, frm, rng, outp = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
TD = '0x' + keccak(b'Donate(bytes32,address,uint256,uint256)').hex()
TS = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
out = {'label': label, 'url': url, 'pm': pm, 'from': frm, 'clientVersionBefore': rpc(url, 'web3_clientVersion', [])}
head = int(rpc(url, 'eth_blockNumber', []), 16); out['head'] = head
don, nsw, mx, q, errs = [], 0, 0, 0, 0
b = frm
import os
deadline = time.time() + float(os.environ.get('DEADLINE_S', '1e9'))
while b <= head:
    if time.time() > deadline: out['stoppedAtDeadline'] = True; break
    e = min(head, b + rng - 1)
    try:
        logs = rpc(url, 'eth_getLogs', [{'address': pm, 'topics': [[TD, TS]], 'fromBlock': hex(b), 'toBlock': hex(e)}], timeout=120); q += 1
    except Exception as ex:
        errs += 1
        if rng > 1 and errs < 400: rng = max(1, rng // 2); time.sleep(1); continue
        raise
    for l in logs:
        if l['topics'][0] == TD:
            d = bytes.fromhex(l['data'][2:])
            don.append({'block': int(l['blockNumber'], 16), 'tx': l['transactionHash'], 'id': l['topics'][1], 'amount0': int.from_bytes(d[:32], 'big'), 'amount1': int.from_bytes(d[32:64], 'big')})
        else:
            nsw += 1; d = bytes.fromhex(l['data'][2:])
            sq = int.from_bytes(d[64:96], 'big'); L = int.from_bytes(d[96:128], 'big')
            mx = max(mx, (L * sq).bit_length())
    b = e + 1
out.update(lastBlockRead=b - 1, queries=q, errorsHalved=errs, finalRange=rng, donates=don, donateCount=len(don), swapCount=nsw, maxLog2LiquidityTimesSqrtPrice=mx,
           clientVersionAfter=rpc(url, 'web3_clientVersion', []))
json.dump(out, open(outp, 'w'), indent=1)
print(label, 'head', head, 'queries', q, 'donates', len(don), 'swaps', nsw, 'maxlog2 L*sqrtP', mx)
