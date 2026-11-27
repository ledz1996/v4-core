"""Run cycle 27 hiword vectors against one URL. Usage: hiword_on.py <out.json> <url> [rounds]"""
import sys, os, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/027/op-stack-eth.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import hiword, battery, evm
out, url = sys.argv[1], sys.argv[2]; rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 1
code = battery.dispatcher(); V = hiword.vectors(); res = []
cv = evm.rpc(url, 'web3_clientVersion', [], 20)
for r in range(rounds):
    done, bad, errors = battery.run(url, code, V, size=300)
    print(url, cv, 'round', r + 1, 'ran', done, '/', len(V), 'mismatches', len(bad), 'errors', len(errors), errors[:1])
    res.append({'url': url, 'clientVersion': cv, 'round': r + 1, 'ran': done, 'vectors': len(V), 'mismatches': bad[:50], 'errors': errors[:5]})
json.dump(res, open(out, 'w'), indent=1)
