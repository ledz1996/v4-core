"""Cycle 18, unit theme-full-range-swaps. Run chosen scripts of set 1 (pmdiff.py) or set 2 (pmdiff2.py) at the fresh
PoolManager address, exactly as the stored references were made (realrun.py of cycle 17 in 'fresh' mode: same
generators, same seeds 7_2026_11_24 and 11_2026_11_24, same overrides), on one endpoint with a chosen gas.

Two calls per script: the plain call to the driver (its answer is hashed and compared with the stored hash and with
other runs), and the same call through a meter at METER, whose code is
  GAS CALLDATACOPY(0,0,cds) CALL(GAS, DRV, 0, 0, cds, 0, 0) GAS ; returns [gasBefore-gasAfter][ok][gasAtEntry][returndata]
so the gas the driver used and the gas the frame had are known. web3_clientVersion is read before and after the batch.
Usage: python3 runfull.py <set> <url> <gas> <out.json> <idx,idx,...> [label]
"""
import sys, os, json, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__))
R17 = '/home/user/v4-core/research/network-risk/cycles/017/theme-real-address-runs.work/scripts'
S, URL, GAS, OUT, IDX = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], [int(x) for x in sys.argv[5].split(',')]
LABEL = sys.argv[6] if len(sys.argv) > 6 else ''
sys.argv = ['realrun.py', S, 'fresh', '1', '/dev/null', '1']
sys.path.insert(0, R17)
import realrun as RR  # noqa
from evm import rpc, assemble  # noqa
RR.URL = URL
_CODE_CACHE = '/home/user/v4-core/research/network-risk/cycles/018/theme-full-range-swaps.work/raw/pm-fresh-code.hex'  # deployed Ethereum PoolManager runtime, immutable rewritten to the fresh address (sha256 a7aaa3ba...)
RR.P.fetch_code = lambda: bytes.fromhex(open(_CODE_CACHE).read())
datas, kinds, drv, ov = RR.build()
METER = '0x00000000000000000000000000000000ae7e0001'
mcode = assemble(['GAS', 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), 'CALLDATACOPY',
                  ('PUSH', 0), ('PUSH', 0), 'CALLDATASIZE', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, int(drv, 16)), 'GAS', 'CALL',
                  'GAS', 'SWAP1', ('PUSH', 32), 'MSTORE', 'DUP2', 'SUB', ('PUSH', 0), 'MSTORE', ('PUSH', 64), 'MSTORE',
                  'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 96), 'RETURNDATACOPY', 'RETURNDATASIZE', ('PUSH', 96), 'ADD', ('PUSH', 0), 'RETURN'])
ovm = dict(ov); ovm[METER] = {'code': '0x' + mcode.hex()}
st = json.load(open(os.path.join(RR.TOOLS, '..', '..', 'opcodes', {'1': 'pmdiff.json', '2': 'pmdiff2.json'}[S])))
refh = st['referenceHashes']
res = json.load(open(OUT)) if os.path.exists(OUT) else {'set': S, 'url': URL, 'gas': GAS, 'label': LABEL, 'batches': [], 'scripts': {}}
def q(m, p):
    try: return rpc(URL, m, p, timeout=30)
    except Exception as e: return 'ERR ' + str(e)[:120]
b = {'clientVersionBefore': q('web3_clientVersion', []), 'blockBefore': q('eth_blockNumber', []), 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'idx': IDX}
for i in IDX:
    r = {}
    plain = RR.ask(datas[i], drv, ov, GAS)
    r['plainErr'] = plain if plain.startswith('ERR') else None
    if not plain.startswith('ERR'):
        r['plainHash'] = hashlib.sha256(bytes.fromhex(plain[2:])).hexdigest(); r['plain'] = plain
        r['equalsStored25M'] = r['plainHash'] == refh[i]
    met = RR.ask(datas[i], METER, ovm, GAS)
    if met.startswith('ERR'): r['meterErr'] = met
    else:
        mb = bytes.fromhex(met[2:])
        r['gasUsed'] = int.from_bytes(mb[:32], 'big'); r['ok'] = int.from_bytes(mb[32:64], 'big'); r['gasAtMeter'] = int.from_bytes(mb[64:96], 'big')
        r['meterPayloadHash'] = hashlib.sha256(mb[96:]).hexdigest()
    res['scripts'][str(i)] = r
    print(S, i, 'plain', r.get('plainHash', r['plainErr'])[:16], 'stored25M', r.get('equalsStored25M'), 'gasUsed', r.get('gasUsed'), 'avail', r.get('gasAtMeter'), 'meterHash', r.get('meterPayloadHash', '')[:16], flush=True)
b['clientVersionAfter'] = q('web3_clientVersion', []); b['blockAfter'] = q('eth_blockNumber', []); b['end'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
res['batches'].append(b)
json.dump(res, open(OUT, 'w'), indent=1)
