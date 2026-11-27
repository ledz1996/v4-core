"""Task 1 (d) and Task 2: TokenRollbackProbe of cycle 16 (cycles/016/theme-revert-rollback-mined.work/TokenRollbackProbe.sol,
runtime from its build/TokenRollbackProbe.json) placed by state override at the deployed PoolManager address, so it holds
the PoolManager's real balances. For each kind (1 revert, 2 invalid, 3 call depth/stack recursion, 4 endless loop, 9 static,
0 control last) it returns ok and four balances before and after: probe and recipient on the token, probe and recipient
in native value. The rule from the specification: a failed or static frame leaves all four words as they were, and the
control moves one unit. The same call runs through eth_simulateV1 where served, and the logs it returns are checked: a
Transfer log may come only from the control frame. For native value, where the chain has no ERC-20 face, the token slot
holds a stub (code override at STUB) that answers every call with a zero word. Read-only.
usage: python3 -I tokprobe.py <out.json> <chainId> <pm> <case-spec-json> <url> [<url> ...]
case-spec: [[label, token|null, mode], ...]"""
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc, version
from evm import keccak, assemble
B = json.load(open('/home/user/v4-core/research/network-risk/cycles/016/theme-revert-rollback-mined.work/build/TokenRollbackProbe.json'))
TO = '0x000000000000000000000000000000000dead032'
STUB = '0x000000000000000000000000000000005707b032'
STUBCODE = assemble([('PUSH', 0x20), ('PUSH', 0), 'RETURN'])
TRANSFER = '0x' + keccak(b'Transfer(address,address,uint256)').hex()
def sel(s): return keccak(s.encode())[:4].hex()
def w(x): return x.to_bytes(32, 'big').hex()
def parse(hexs):
    b = bytes.fromhex(hexs[2:]); ws = [int.from_bytes(b[i:i + 32], 'big') for i in range(64, len(b), 32)]
    rows = [ws[i:i + 10] for i in range(0, len(ws), 10)]
    leaks = [x[0] for x in rows if x[0] != 0 and x[2:6] != x[6:10]]
    c = [x for x in rows if x[0] == 0][0]
    return {'rows': [[str(v) for v in r] for r in rows], 'leaks': leaks, 'controlMoved': c[1] == 1 and c[2:6] != c[6:10],
            'staticRefused': [x for x in rows if x[0] == 9][0][1] == 0, 'failedKindsOk': [x[0] for x in rows if x[0] not in (0,) and x[1] == 1]}
def main():
    out_path, chain, pm, spec = sys.argv[1], int(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4])
    out = []
    for url in sys.argv[5:]:
        res = {'url': url, 'chain': chain, 'before': version(url, chain), 'cases': []}
        blk = rpc(url, 'eth_getBlockByNumber', ['latest', False]); bn = (blk.get('result') or {}).get('number') or 'latest'; res['block'] = bn
        for label, tok, mode in spec:
            t = tok or STUB
            ov = {pm: {'code': '0x' + B['runtime']}}
            if tok is None: ov[STUB] = {'code': '0x' + STUBCODE.hex()}
            data = '0x' + sel('run(address,address,uint256,uint256)') + w(int(t, 16)) + w(int(TO, 16)) + w(1) + w(mode)
            tx = {'from': '0x00000000000000000000000000000000000a11ce', 'to': pm, 'data': data, 'gas': hex(20_000_000)}
            rec = {'label': label, 'token': t, 'mode': mode}
            r = rpc(url, 'eth_call', [tx, bn, ov], 120); rec['ethCall'] = r
            if 'result' in r:
                try: rec.update(parse(r['result']))
                except Exception as e: rec['parseErr'] = str(e)
            s = rpc(url, 'eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': ov, 'calls': [tx]}], 'validation': False}, bn], 120)
            rec['simulate'] = s
            try:
                c0 = s['result'][0]['calls'][0]; rec['simStatus'] = c0.get('status')
                logs = c0.get('logs', [])
                rec['simLogs'] = [{'address': l['address'], 'topics': l['topics'], 'data': l['data']} for l in logs]
                rec['simTransferLogs'] = len([l for l in logs if l['topics'] and l['topics'][0] == TRANSFER])
                rec['simReturnEqualsCall'] = c0.get('returnData') == r.get('result')
            except Exception as e: rec['simErr'] = str(e)[:100]
            if 'simTransferLogs' not in rec:
                tr = rpc(url, 'debug_traceCall', [tx, bn, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}, 'stateOverrides': ov}], 120)
                rec['traceCall'] = {'error': tr.get('error')} if 'result' not in tr else 'ok'
                if 'result' in tr:
                    kept = []
                    def walk(f, failed):
                        failed = failed or bool(f.get('error'))
                        for l in f.get('logs', []) or []:
                            if l.get('topics') and l['topics'][0] == TRANSFER: kept.append({'address': l['address'], 'topics': l['topics'], 'data': l.get('data'), 'inFailedFrame': failed})
                        for c in f.get('calls', []) or []: walk(c, failed)
                    walk(tr['result'], False)
                    rec['traceTransferLogs'] = kept
            res['cases'].append(rec)
            print(chain, url, label, 'leaks', rec.get('leaks'), 'control', rec.get('controlMoved'), 'static', rec.get('staticRefused'),
                  'simTransfers', rec.get('simTransferLogs'), 'simEq', rec.get('simReturnEqualsCall'), 'trace', None if 'traceTransferLogs' not in rec else [(l['address'][:8], l['inFailedFrame']) for l in rec['traceTransferLogs']], '' if 'result' in r else json.dumps(r)[:200])
        res['after'] = version(url, chain); out.append(res)
    json.dump(out, open(out_path, 'w'), indent=1)
main()
