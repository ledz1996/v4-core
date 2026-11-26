"""Which conditional jump sides of the build this unit's cases execute (reference EVM, per case), whether the four
sides left by cycle 25 now run, and which of the 387 jumps x 2 sides no case of cycles 25 and 26 has run.
Usage: python3 coverage26.py <ref-1.json of cycle 26> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import NR, pm_build
code = pm_build(0x000000000004444c5dc75cB358380D2e3dE08A90)
jumps = []; i = 0
while i < len(code):
    op = code[i]
    if op == 0x57: jumps.append(i)
    i += op - 0x5e if 0x60 <= op <= 0x7f else 1
jm = json.load(open(os.path.join(NR, 'opcodes', 'jumpmap.json')))
ref = json.load(open(sys.argv[1]))
c25 = json.load(open(os.path.join(NR, 'cycles', '025', 'theme-unexecuted-sides.work', 'out', 'ref-1.json')))
cases = {str(c['id']): c['tag'] for c in json.load(open(os.path.join(os.path.dirname(sys.argv[1]), 'cases.json')))['cases']}
first = {}
for cid, ks in ref['perCaseSides'].items():
    for k in ks: first.setdefault(k, cases[cid])
targets = {'6230:1': 'PoolManager.sol:181 hook delta accounted', '18977:1': 'Pool.sol:320 amount to swap zero',
           '13447:1': 'PoolManager.sol:356 NonzeroNativeValue', '12839:1': 'Currency.sol:51 native payout failed'}
tres = {k: {'what': v, 'count': ref['sides'].get(k, 0), 'firstCase': first.get(k)} for k, v in targets.items()}
mine = set(ref['sides']); prev = set(c25['sides']) | set(k for k in c25.get('perCaseSides', {}).get('outside', []))
allsides = ['%d:%d' % (pc, s) for pc in jumps for s in (0, 1)]
src = {}
for r in jm.get('oneSided', []) + jm.get('neverReached', []): src[r['pc']] = r['src']
neither = [k for k in allsides if k not in mine and k not in prev]
newly = [k for k in allsides if k in mine and k not in prev]
out = {'jumps': len(jumps), 'sides': len(allsides), 'executedHere': len(mine & set(allsides)), 'executedCycle25': len(prev & set(allsides)),
       'union': len((mine | prev) & set(allsides)), 'targets': tres, 'newVsCycle25': [{'side': k, 'firstCase': first.get(k)} for k in newly],
       'notRunByCycle25or26': [{'side': k, 'src': src.get(int(k.split(':')[0]))} for k in neither]}
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print({k: v for k, v in out.items() if k in ('jumps', 'sides', 'executedHere', 'executedCycle25', 'union')})
for k, v in tres.items(): print(k, v)
print('new vs cycle 25', len(newly)); print('not run', len(neither))
