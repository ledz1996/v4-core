"""debug_traceCall (callTracer) of one sequence on one endpoint, read-only, bracketed by web3_clientVersion.
Usage: python3 -I tracecall.py <chainId> <url> <seq> <out.json> [gas]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
from evm import rpc
cid, url, nm, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
gas = int(sys.argv[5]) if len(sys.argv) > 5 else 25_000_000
n = {x['chainId']: x for x in json.load(open(os.path.join(S.NR, 'state', 'networks.json')))['networks']}[cid]
pm = int(n['poolManager'], 16)
salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
st = S.sequences(salt)[nm]
rec = {'clientBefore': rpc(url, 'web3_clientVersion', [])}
blk = rpc(url, 'eth_blockNumber', []); rec['block'] = int(blk, 16)
tx = {'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.D, 'data': '0x' + S.enc_run(st).hex(), 'gas': hex(gas)}
try:
    rec['trace'] = rpc(url, 'debug_traceCall', [tx, blk, {'tracer': 'callTracer', 'stateOverrides': S.overrides(pm)}], timeout=300)
except Exception as e:  # noqa
    rec['error'] = str(e)[:500]
rec['clientAfter'] = rpc(url, 'web3_clientVersion', [])
json.dump(rec, open(out, 'w'))
print({k: v for k, v in rec.items() if k != 'trace'})
