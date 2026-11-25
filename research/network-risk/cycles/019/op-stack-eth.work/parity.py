"""L-092 / L5: compare each unit chain's deployed PoolManager runtime with the runtime built from this checkout
(research/network-risk/build/PoolManager.json), after writing the chain's own address into the one immutable."""
import json, urllib.request, sys
B = json.load(open('../../../build/PoolManager.json'))
rt = bytes.fromhex(B['runtime']); imm = B['immutableReferences']['1375'][0]
def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), headers={"content-type":"application/json","user-agent":"rpc-check"})
    return json.load(urllib.request.urlopen(r, timeout=60))['result']
nets = [n for n in json.load(open('../../../state/networks.json'))['networks'] if n['chainId'] in (10,8453,130,7777777,480,57073,1868)]
out = {}
for n in nets:
    code = bytes.fromhex(rpc(n['rpc'], 'eth_getCode', [n['poolManager'], 'latest'])[2:])
    mine = bytearray(rt); mine[imm['start']:imm['start']+32] = bytes(12) + bytes.fromhex(n['poolManager'][2:])
    mine = bytes(mine)
    pre = 0
    while pre < min(len(code), len(mine)) and code[pre] == mine[pre]: pre += 1
    suf = 0
    while suf < min(len(code), len(mine)) - pre and code[-1-suf] == mine[-1-suf]: suf += 1
    ndiff = sum(1 for a, b in zip(code, mine) if a != b) if len(code) == len(mine) else None
    row = {'len': len(code), 'buildLen': len(mine), 'equal': code == mine, 'commonPrefix': pre, 'commonSuffix': suf, 'bytesDiffering': ndiff,
           'deployedTail': code[pre:pre+96].hex() if code != mine else '', 'buildTail': mine[pre:pre+96].hex() if code != mine else ''}
    out[n['chainId']] = row; print(n['chainId'], json.dumps(row))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
