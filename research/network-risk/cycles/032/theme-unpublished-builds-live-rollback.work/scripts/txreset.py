"""Transient storage reset between transactions, through eth_simulateV1 where served. Contract T (code override):
calldata empty -> returns [TLOAD(5), SLOAD(5)] then TSTORE(5, 7) and SSTORE(5, 9) via a second entry; calldata non-empty
-> writes. Calls in one simulated block: write, read; then a second simulated block: read. Specification: the reads
return TLOAD 0 (transient storage is cleared at the end of each transaction, EIP-1153) and SLOAD 9. Read-only.
usage: python3 -I txreset.py <out.json> <chainId> <url>..."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc, version
from evm import assemble
T = '0x00000000000000000000000000000000ee1153a0'
code = assemble(['CALLDATASIZE', ('REF', 'wr'), 'JUMPI', ('PUSH', 5), 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 5), 'SLOAD', ('PUSH', 32), 'MSTORE',
                 ('PUSH', 64), ('PUSH', 0), 'RETURN', ('LABEL', 'wr'), ('PUSH', 7), ('PUSH', 5), 'TSTORE', ('PUSH', 9), ('PUSH', 5), 'SSTORE', 'STOP'])
FROM = '0x00000000000000000000000000000000000c0de1'
out = []
for u in sys.argv[3:]:
    b = version(u, int(sys.argv[2]))
    c = lambda d: {'from': FROM, 'to': T, 'data': d, 'gas': hex(100000)}
    r = rpc(u, 'eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': {T: {'code': '0x' + code.hex()}}, 'calls': [c('0x01'), c('0x')]}, {'calls': [c('0x')]}], 'validation': False}, 'latest'])
    rec = {'url': u, 'before': b, 'resp': r, 'after': version(u, int(sys.argv[2]))}
    try:
        rd = [x['calls'][-1]['returnData'] for x in r['result']]
        rec['reads'] = rd; rec['ok'] = all(x == '0x' + '00' * 32 + '00' * 31 + '09' for x in rd)
    except Exception as e: rec['err'] = json.dumps(r)[:200]
    print(u, b['web3_clientVersion'].get('result'), rec.get('reads'), rec.get('ok'), rec.get('err', ''))
    out.append(rec)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
