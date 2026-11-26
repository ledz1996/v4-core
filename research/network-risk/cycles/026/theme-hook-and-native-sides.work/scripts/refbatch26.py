"""Reference EVM run with the same batches as a network run (cases of one eth_call share one world there, so native
balances carry over between cases of a batch). Usage: python3 refbatch26.py <cases.json> <chain-<id>.json> <out.json>
The real native balance of address(0) on each chain is unknown to the reference; compare26.py masks that one word."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import enc_run, dec_run, codes_for, balances_for, D, EOA
import pyevm26 as P
cases = {c['id']: c for c in json.load(open(sys.argv[1]))['cases']}
ch = json.load(open(sys.argv[2])); pm = int(ch['pm'], 16)
out = {'pm': hex(pm), 'chainFile': os.path.basename(sys.argv[2]), 'results': {}}
for b in ch['batches']:
    if 'error' in b: continue
    chunk = [cases[i] for i in b['ids']]
    w = P.World(codes_for(pm, chunk), balances_for(pm))
    try:
        ok, ret = w.call(EOA, D, 0, enc_run(chunk, pm), False, 0)
    except NotImplementedError as e:
        for c in chunk: out['results'][str(c['id'])] = {'notImplemented': str(e)}
        continue
    if not ok:
        for c in chunk: out['results'][str(c['id'])] = {'topFail': ret.hex()}
        continue
    for c, (uok, words, rv) in zip(chunk, dec_run(ret)):
        out['results'][str(c['id'])] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
json.dump(out, open(sys.argv[3], 'w'))
print('done', len(out['results']))
