"""Read owner, protocolFeeController, their code lengths and the PoolManager code hash on each chain. eth_call / eth_getCode only."""
import sys, json, hashlib
sys.path.insert(0, sys.argv[1]); from evm import rpc
nets = json.load(open(sys.argv[2]))['networks']; out = {}
for n in nets:
    if n['chainId'] not in (10, 8453, 130, 7777777, 480, 57073, 1868): continue
    u, pm = n['rpc'], n['poolManager']; r = {'rpc': u, 'block': int(rpc(u, 'eth_blockNumber', []), 16)}
    code = bytes.fromhex(rpc(u, 'eth_getCode', [pm, 'latest'])[2:]); r['codeLen'] = len(code); r['codeSha256'] = hashlib.sha256(code).hexdigest()[:16]
    for name, sel in (('owner', '0x8da5cb5b'), ('protocolFeeController', '0xf02de3b2')):
        a = '0x' + rpc(u, 'eth_call', [{'to': pm, 'data': sel}, 'latest'])[-40:]; r[name] = a
        r[name + 'CodeLen'] = (len(rpc(u, 'eth_getCode', [a, 'latest'])) - 2) // 2
        r[name + 'Same'] = a.lower() == n[name].lower()
    r['ownerCodeSame'] = r['ownerCodeLen'] == n['ownerCodeLen']; r['pfcCodeSame'] = r['protocolFeeControllerCodeLen'] == n['pfcCodeLen']
    r['codeSame'] = r['codeSha256'].startswith(n['codeSha256'])
    out[n['chainId']] = r; print(n['chainId'], json.dumps(r))
json.dump(out, open(sys.argv[3], 'w'), indent=1)
