"""Rerun one Arc set-aside transaction that stopped at the 40,000,000 step limit with a higher limit (lazyreplay24.MAX_STEPS).
usage: steplimit.py <hash> <limit>"""
import json, sys, collections
sys.path.insert(0, '.')
import lazyreplay24 as L
D = json.load(open('../../../023/stablecoin-l1.work/l997/raw/txs.json'))
h = sys.argv[1]; L.MAX_STEPS = int(sys.argv[2]); L.MAX_ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 60
tx, rec = D['tx'][h]['tx'], D['tx'][h]['rec']; blk = D['blocks'][str(int(tx['blockNumber'], 16))]
base, w, ok, ret, err, rounds = L.replay('https://rpc.mainnet.arc.io', tx, rec, blk)
w = w or base.w
ol = [('0x%040x' % a, ['0x%064x' % t for t in tp], '0x' + d.hex()) for a, tp, d in w.logs]
rl = [(l['address'].lower(), [x.lower() for x in l['topics']], l['data'].lower()) for l in rec['logs']]
print(json.dumps({'tx': h, 'rounds': rounds, 'err': err, 'ok': ok, 'steps': w.steps, 'logs': len(ol), 'chainLogs': len(rl), 'logsEqual': ol == rl,
                  'creates': getattr(w, 'creates', 0), 'topOps': collections.Counter(w.ops).most_common(5), 'gasUsed': int(rec['gasUsed'], 16)}))
