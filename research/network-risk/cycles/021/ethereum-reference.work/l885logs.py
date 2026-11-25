"""L-885: every log the Ethereum copy at 0x8366a39c... has emitted since creation. Read-only eth_getLogs."""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
A = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
U = 'https://ethereum.public.blockpi.network/v1/rpc/public'
start, head = 25466547, int(rpc(U, 'eth_blockNumber', []), 16)
logs = []; b = start; n = 0
while b <= head:
    e = min(b + 4999, head)
    for k in range(5):
        try:
            logs += rpc(U, 'eth_getLogs', [{'address': A, 'fromBlock': hex(b), 'toBlock': hex(e)}]); break
        except Exception as ex:
            time.sleep(2 * (k + 1))
    else:
        raise SystemExit('failed at %d' % b)
    b = e + 1; n += 1
topics = {}
for l in logs: topics[l['topics'][0]] = topics.get(l['topics'][0], 0) + 1
out = {'from': start, 'to': head, 'requests': n, 'logs': len(logs), 'byTopic0': topics, 'sample': logs[:5]}
json.dump(out, open('l885logs.json', 'w'), indent=1); print(json.dumps(out, indent=1)[:3000])
