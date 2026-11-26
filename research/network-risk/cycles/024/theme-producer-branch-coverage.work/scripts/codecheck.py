"""Fetch the deployed PoolManager code on the given chains (eth_getCode, latest), bracketed with web3_clientVersion, and compare
with build/PoolManager.json runtime with its immutable set to the PoolManager address. usage: codecheck.py <cid>..."""
import sys, json, urllib.request, hashlib, time
from replaycov import code_for, NETS
from pyevm_cov import keccak
def rpc(u, m, p):
    r = urllib.request.Request(u, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=60))
out = {}
for c in map(int, sys.argv[1:]):
    n = NETS[c]; u = n['rpc'] if 'rpc' in n else n.get('rpcUrl'); pm = n['poolManager']
    a = rpc(u, 'web3_clientVersion', []); code = rpc(u, 'eth_getCode', [pm, 'latest']); b = rpc(u, 'web3_clientVersion', [])
    got = bytes.fromhex(code['result'][2:]); exp = code_for(pm.lower())
    out[c] = {'url': u, 'clientBefore': a.get('result', a.get('error')), 'clientAfter': b.get('result', b.get('error')), 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'len': len(got), 'keccak': '0x' + keccak(got).hex(), 'equalsBuildWithImmutable': got == exp}
    print(c, out[c])
json.dump(out, open('../out/codecheck.json', 'w'), indent=1)
