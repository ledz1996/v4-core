"""Per-network totals from raw/r2-<chainId>.json and raw/samples*.json into totals.json."""
import json, glob
from endpoints import NETS
S = {}
for f in glob.glob('raw/samples*.json'):
    for r in json.load(open(f))['results']:
        k = (r['chainId'], r['tx'], r['pool'], r['a0'])
        if r.get('ok') or k not in S: S[k] = r
out = []
for cid in [n for n in NETS]:
    try: d = json.load(open(f'raw/r2-{cid}.json'))
    except FileNotFoundError: continue
    sm = [r for k, r in S.items() if k[0] == cid]
    z = d.get('zeroAmount') or {}
    out.append({'chainId': cid, 'name': d['name'], 'blocks': d['blocks'], 'swaps': d['swaps'], 'tick': d['tick'],
                'singleStep': sum(d['single'].values()), 'fullLoop': d['fullLoop'], 'fullLoopModes': d.get('loopModes'), 'fullLoopKey': d.get('loopKey'),
                'fullLoopHooks': d.get('loopHooks'), 'zeroAmount': {k: v for k, v in z.items() if k != 'samples'}, 'setAside': d['setAside'],
                'unmatched': len(d['unmatched']), 'maxSteps': d['maxSteps'], 'feeCheck': {k: v for k, v in d['feeCheck'].items() if k != 'mismatches'},
                'feeGrowth': {'checked': d['feeGrowth']['checked'], 'match': d['feeGrowth']['match']}, 'initInWindow': d.get('initInWindow', 0),
                'storedSamples': {'n': len(sm), 'replayed': sum(1 for r in sm if r.get('ok')), 'keyKnown': sum(1 for r in sm if r.get('keyKnown')),
                                  'maxSteps': max([r.get('steps', 0) for r in sm if r.get('ok')] or [0])}})
tot = {k: sum(o[k] for o in out) for k in ('swaps', 'singleStep', 'fullLoop', 'unmatched')}
tot['setAside'] = sum(sum(o['setAside'].values()) for o in out)
tot['zeroAmount'] = sum(sum(o['zeroAmount'].values()) for o in out)
tot['samples'] = sum(o['storedSamples']['n'] for o in out); tot['samplesReplayed'] = sum(o['storedSamples']['replayed'] for o in out)
tot['feeGrowthChecked'] = sum(o['feeGrowth']['checked'] for o in out); tot['feeGrowthMatch'] = sum(o['feeGrowth']['match'] for o in out)
tot['feeStatic'] = sum(o['feeCheck']['static'] for o in out); tot['feeStaticMismatch'] = sum(o['feeCheck']['staticMismatch'] for o in out)
tot['tickMismatch'] = sum(o['tick']['mismatch'] for o in out)
json.dump({'totals': tot, 'networks': out}, open('totals.json', 'w'), indent=1)
print(json.dumps(tot))
for o in out: print(o['chainId'], o['name'], o['swaps'], o['singleStep'], o['fullLoop'], o['fullLoopKey'], o['zeroAmount'], o['setAside'], o['unmatched'], o['storedSamples'], o['maxSteps'])
