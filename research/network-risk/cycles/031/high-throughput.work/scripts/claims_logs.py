# L-1214: search PoolManager ERC-6909 Transfer (between two nonzero accounts), Approval and OperatorSet logs.
import json, sys, urllib.request, time
from hashlib import sha3_256
RPC, PM, FROM, TO, STEP, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
# keccak via evm.py
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
def k(s): return '0x' + keccak(s.encode()).hex()
T = {'Transfer': k('Transfer(address,address,address,uint256,uint256)'), 'Approval': k('Approval(address,address,uint256,uint256)'), 'OperatorSet': k('OperatorSet(address,address,bool)')}
def call(m, p):
    for a in range(6):
        try:
            req = urllib.request.Request(RPC, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), {'content-type':'application/json','user-agent':'curl/8.5.0'})
            r = json.load(urllib.request.urlopen(req, timeout=120))
            if 'error' in r: raise Exception(str(r['error']))
            return r['result']
        except Exception as e:
            if a == 5: raise
            time.sleep(2*(a+1))
found = {n: [] for n in T}; cnt = {n: 0 for n in T}; b = FROM; reqs = 0; errs = []
step = STEP
while b <= TO:
    e = min(TO, b + step - 1)
    try:
        logs = call('eth_getLogs', [{"address": PM, "fromBlock": hex(b), "toBlock": hex(e), "topics": [[T['Transfer'], T['Approval'], T['OperatorSet']]]}])
    except Exception as ex:
        if step > 100: step //= 4; continue
        errs.append([b, e, str(ex)[:200]]); b = e + 1; continue
    reqs += 1
    for l in logs:
        n = [x for x in T if T[x] == l['topics'][0]][0]
        if n == 'Transfer':
            fr, to = l['topics'][1][-40:], l['topics'][2][-40:]
            if int(fr, 16) == 0 or int(to, 16) == 0: continue
        cnt[n] += 1
        if len(found[n]) < 20: found[n].append({'block': int(l['blockNumber'], 16), 'tx': l['transactionHash']})
    b = e + 1
json.dump({'rpc': RPC, 'from': FROM, 'to': TO, 'requests': reqs, 'counts': cnt, 'samples': found, 'errors': errs, 'topics': T}, open(OUT, 'w'), indent=1)
print(cnt, 'requests', reqs, 'errors', len(errs))
