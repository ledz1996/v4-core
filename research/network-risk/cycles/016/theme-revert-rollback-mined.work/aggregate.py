"""Summarise scans and replays of this unit into raw/summary.json (read-only over local files)."""
import json, glob, os
EP = {'0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789', '0x0000000071727de22e5e9d8baf0edac6f37da032', '0x4337084d9e255ff0702461cf8895ce9e3b5ff108'}
out = {}
for f in sorted(glob.glob('raw/scan_[0-9]*.json')):
    d = json.load(open(f)); s = d['summary']; c = s['chain']
    hits = d['hits']
    ex = [h['tx'] for h in hits if h['revertedThenCompletedUnlock']][:3]
    pay = [h['tx'] for h in hits if any(p[1] and p[0] in ('sync', 'settle', 'take', 'mint', 'settleFor', 'burn') for p in h['pm'])][:3]
    out[c] = {'scan': s, 'exampleRevertedThenCompletedUnlock': ex, 'exampleUndonePayment': pay}
for f in sorted(glob.glob('raw/replay_[0-9]*.json')):
    c = int(os.path.basename(f)[7:-5]); R = json.load(open(f))
    run = [r for r in R if 'pmChain' in r]
    def logs_ok(r):
        if r['logsEqual']: return True
        return False
    rs = {'replayed': len(run), 'unsupported': [r['unsupported'] for r in R if 'unsupported' in r], 'errors': sum('error' in r for r in R),
          'statusEqual': sum(r['statusChain'] == r['statusRef'] for r in run), 'pmFramesEqual': sum(r['pmFramesEqual'] for r in run),
          'pmFrames': sum(r['pmFramesChain'] for r in run), 'logsEqual': sum(r['logsEqual'] for r in run),
          'logsDifferOnlyInEntryPoint': sum((not r['logsEqual']) and r['logsChain'] == r['logsRef'] and all(a in EP for a in r['extraChainLogs']) for r in run),
          'slots': sum(r['slotsCompared'] for r in run), 'pmSlots': sum(r['pmSlotsCompared'] for r in run),
          'storageMismatch': sum(len(r['storageMismatch']) for r in run), 'txs': [r['tx'] for r in run]}
    sc = {h['tx']: h for h in json.load(open(f'raw/scan_{c}.json'))['hits']}
    rs['withRevertedThenCompletedUnlock'] = sum(sc[r['tx']]['revertedThenCompletedUnlock'] for r in run if r['tx'] in sc)
    rs['withUndonePayment'] = sum(any(p[1] and p[0] in ('sync', 'settle', 'take', 'mint', 'settleFor', 'burn') for p in sc[r['tx']]['pm']) for r in run if r['tx'] in sc)
    rs['undonePmFramesInReplayed'] = sum(sum(p[1] for p in sc[r['tx']]['pm']) for r in run if r['tx'] in sc)
    out.setdefault(c, {})['replay'] = rs
json.dump(out, open('raw/summary.json', 'w'), indent=1)
for c, v in out.items():
    print(c, json.dumps({k: v['scan'][k] for k in ('txs', 'traced', 'statusMismatch', 'logsMismatch', 'undoneThenOkTx', 'revertedThenCompletedUnlockTx', 'blocks')}) if 'scan' in v else '', json.dumps({k: v['replay'][k] for k in v.get('replay', {}) if k != 'txs'}) if 'replay' in v else '')
