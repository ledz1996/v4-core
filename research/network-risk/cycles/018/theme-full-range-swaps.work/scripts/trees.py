"""Fetch the callTracer tree of each full-range script with debug_traceCall (fresh-address form, as runfull.py) and
write the line format read by cycle 16's replay.cpp (rp = monad v0.16.7, rp165 = v0.16.5): the PoolManager frames are
re-executed by Monad's interpreter and by native code from Monad's emitter, every other call is answered from the tree.
Usage: python3 trees.py <url> <gas> <out.txt> <set:idx,...>"""
import sys, os, json, gzip, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__))
R17 = os.path.join(HERE, '..', '..', '..', '017', 'theme-real-address-runs.work', 'scripts')
URL, GAS, OUTP, SPEC = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.argv = ['realrun.py', '1', 'fresh', '1', '/dev/null', '1']; sys.path.insert(0, R17)
import realrun as RR  # noqa
from evm import rpc  # noqa
RR.P.fetch_code = lambda: bytes.fromhex(open(os.path.join(HERE, '..', 'raw', 'pm-fresh-code.hex')).read())
FRESH = RR.P.PM.lower()
built = {}
for st in ('1', '2'):
    RR.SET = st; built[st] = RR.build()
def h(x):
    x = (x or '0x')[2:]
    if len(x) % 2: x = '0' + x
    return x if x else '-'
def num(x): return str(int(x, 16)) if x else '0'
out = open(OUTP, 'w'); meta = {'url': URL, 'gas': GAS, 'clientVersionBefore': rpc(URL, 'web3_clientVersion', []), 'scripts': {}}
for part in SPEC.split(','):
    st, i = part.split(':'); i = int(i); datas, kinds, drv, ov = built[st]
    t = None
    for k in range(5):
        try: t = rpc(URL, 'debug_traceCall', [{'to': drv, 'data': '0x' + datas[i].hex(), 'gas': hex(GAS)}, 'latest', {'stateOverrides': ov, 'tracer': 'callTracer'}], timeout=300); break
        except Exception as e: time.sleep(6 * (k + 1)); err = str(e)
    if t is None: meta['scripts'][part] = {'error': err[:200]}; continue
    json.dump(t, gzip.open(os.path.join(HERE, '..', 'raw', os.environ.get('TREEDIR', 'trees'), f's{st}-{i}.json.gz'), 'wt'))
    oh = hashlib.sha256(bytes.fromhex(t['output'][2:])).hexdigest()
    out.write(f"TX s{st}-{i} 1 1 1 0 {'00' * 20} {'00' * 20} 0 0 150000000\n")
    out.write(f"BAL {'8ac7230489e80000' if st == '2' else '0'}\n")
    ids = [0]; npm = [0]
    def walk(node, parent):
        n_ = ids[0]; ids[0] += 1; to = (node.get('to') or '').lower()
        pm = 1 if to == FRESH and node.get('type') in ('CALL', 'STATICCALL') else 0; npm[0] += pm
        e = node.get('error') or ''; oog = 1 if 'gas' in e.lower() else 0
        out.write(f"N {n_} {parent} {pm} {node.get('type')} {to[2:] if to else '-'} {node['from'][2:]} {h(node.get('value', '0x0'))} {num(node.get('gas'))} {num(node.get('gasUsed'))} {0 if e else 1} {oog} {h(node.get('input'))} {h(node.get('output'))}\n")
        for c in node.get('calls') or []: walk(c, n_)
    walk(t, -1)
    meta['scripts'][part] = {'outputHash': oh, 'nodes': ids[0], 'pmFrames': npm[0], 'gasUsed': int(t['gasUsed'], 16)}
    print(part, oh[:16], 'nodes', ids[0], 'pm frames', npm[0], flush=True)
meta['clientVersionAfter'] = rpc(URL, 'web3_clientVersion', [])
json.dump(meta, open(OUTP + '.meta.json', 'w'), indent=1)
