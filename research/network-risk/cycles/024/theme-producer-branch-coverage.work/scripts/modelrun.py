"""Replay fetched transactions through cycle 23's source model (theme-state-replay.work/scripts/model.py): frame outputs,
PoolManager logs, hook calldata and every changed storage word. usage: modelrun.py <cid> <dir>  writes <dir>/model-result.json"""
import sys, json, gzip, glob
sys.setrecursionlimit(20000)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
import model as M
from eps import NETS
cid = int(sys.argv[1]); d = sys.argv[2]; PM = NETS[cid]['poolManager'].lower()
res = []
for fn in sorted(glob.glob(d + '/*.json.gz')):
    rec = json.load(gzip.open(fn))
    pre = next((v for k, v in rec['pre'].items() if k.lower() == PM), {})
    dpre = next((v for k, v in rec['diff']['pre'].items() if k.lower() == PM), {})
    dpost = next((v for k, v in rec['diff']['post'].items() if k.lower() == PM), {})
    m = M.Model(PM, pre.get('storage'), M.I(pre.get('balance')))
    err = None
    try: m.frame(rec['call']); m.finish(dpre, dpost)
    except Exception as e: err = repr(e)[:300]
    res.append({'hash': rec['hash'], 'block': rec['block'], 'wordsCompared': m.words_compared, 'mismatches': list(m.mm), 'unread': [hex(x) for x in sorted(m.unread)][:10], 'error': err,
                'actions': [a[0] for a in m.actions]})
    print(res[-1]['hash'][:12], res[-1]['wordsCompared'], len(res[-1]['mismatches']), err, res[-1]['actions'][:8])
json.dump(res, open(d + '/model-result.json', 'w'), indent=1)
