"""Copied from cycle 24 theme-failed-tx-replay for cycle 25 theme-avalanche-sae; only paths changed (window and model now from this work directory).
Tasks 1 and 3 (cycle 24, theme-failed-tx-replay): replay traced transactions through the cycle 23 source model.
usage: analyze.py <chainId> [rawTxParentDir] [tag]   (with the cycle 23 raw dir, kind c23success: caught PoolManager reverts in successful transactions)
Failed transactions (receipt status 0): every frame is replayed in order; a frame that failed on chain has its children replayed
and the model state is rolled back after it, as the EVM does. Each PoolManager frame that failed on chain is classified:
  source      the model, run from the replayed state, raises the same source revert (custom error, Panic 0x11, empty revert of a
              non-payable or undecodable call), or the frame bubbles or wraps a failed child exactly as the source does
              (src/PoolManager.sol:110, src/libraries/Hooks.sol:137, src/types/Currency.sol:51-53,82-90,94), or the frame has a
              selector the PoolManager does not implement (no fallback, empty revert)
  oog         the frame, or the child whose failure it carries, ran out of gas (error string, or gasUsed equal to gas)
  unexplained anything else; written out in full
Successful frames inside failed transactions are compared word by word as in cycle 23 (outputs, logs are cleared by the tracer).
Log-free successful transactions (task 3) are replayed as cycle 23 run.py did: outputs, every changed storage word, native balance.
Writes results/replay-<cid>.json and results/replay-<cid>-records.jsonl (every classification and every mismatch in full)."""
import json, os, sys, gzip, glob, collections, traceback
sys.setrecursionlimit(20000)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/025/theme-avalanche-sae.work/scripts')
import model as M
from model import Model, Revert, Unmodelled, I
from eps import NETS
HERE = os.path.dirname(os.path.abspath(__file__))
SEL = json.load(open(HERE + '/../results/selectors.json'))
NAME = {k: v[0].split('(')[0] for k, v in SEL.items()}
cid = int(sys.argv[1]); PM = NETS[cid]['poolManager'].lower()
D = sys.argv[2] if len(sys.argv) > 2 else HERE + '/../raw/%d' % cid
TAG = sys.argv[3] if len(sys.argv) > 3 else ''
WRAPPED = '0x90bfb865'

def oog(f):
    e = (f.get('error') or '').lower()
    return 'out of gas' in e or 'gas' in e and 'revert' not in e or (f.get('gas') and f.get('gasUsed') and I(f['gas']) == I(f['gasUsed']) and not f.get('output'))

class FModel(Model):
    def __init__(s, *a):
        super().__init__(*a); s.cls = []; s.fail_depth = 0; s.logs_cleared = 0
    def mis(s, kind, **kw):
        # callTracer drops the logs of every frame that failed and of all frames below it, so a missing log under a failed
        # frame is what the tracer does, not a PoolManager difference; it is counted, not reported
        if kind == 'log-missing' and s.fail_depth > 0: s.logs_cleared += 1; return
        Model.mis(s, kind, **kw)
    def frame(s, f):
        if not f.get('error'):
            return Model.frame(s, f)
        snap = s.snap(); to = (f.get('to') or '').lower(); s.fail_depth += 1
        if to == s.pm and f.get('type') in ('CALL', 'STATICCALL'):
            s.cls.append(s.classify(f))
        else:
            g = dict(f); g['error'] = None
            try: Model.frame(s, g)
            except (Revert,) as e: pass
        s.fail_depth -= 1
        s.restore(snap)
    def classify(s, f):
        out = f.get('output') or '0x'; sel = out[:10] if len(out) >= 10 else out
        rec = {'pmSelector': (f.get('input') or '')[:10], 'call': M.S.get((f.get('input') or '')[2:10]), 'from': f.get('from'), 'error': f.get('error'),
               'output': out, 'decoded': SEL.get(sel, [None])[0], 'gas': f.get('gas'), 'gasUsed': f.get('gasUsed')}
        kids = f.get('calls', []) or []
        bad = [c for c in kids if c.get('error')]
        mmn = len(s.mm); pred = None
        try:
            Model.pm_call(s, f); pred = 'success'
        except Revert as e: pred = str(e)
        except Unmodelled as e: pred = 'unmodelled: %s' % e
        rec['model'] = pred
        new = s.mm[mmn:]; del s.mm[mmn:]
        if any(x['kind'] == 'unlock-ended-unsettled' for x in new) and pred == 'success': pred = rec['model'] = 'CurrencyNotSettled'
        rec['modelNotes'] = [x['kind'] for x in new]
        name = NAME.get(sel)
        # 1. out of gas
        if oog(f) and not bad: rec['class'] = 'oog'; rec['why'] = 'frame ran out of gas'; return rec
        # 2. failed child carried up
        if bad:
            c = bad[-1]; co = c.get('output') or '0x'
            if co == out or (out in ('0x', '') and oog(c)):
                rec['class'] = 'oog' if (oog(c) and out in ('0x', '')) else 'source'
                rec['why'] = 'bubbles the failed child %s %s (%s)' % (c.get('to'), (c.get('input') or '')[:10], 'out of gas' if oog(c) else 'same revert data')
                rec['origin'] = deepest(c); return rec
            if sel == WRAPPED:
                w = out[10:]; tgt = '0x' + w[24:64]
                rec['class'] = 'source' if tgt.lower() == (c.get('to') or '').lower() else 'unexplained'
                rec['why'] = 'WrappedError around the failed child %s' % c.get('to'); rec['origin'] = deepest(c); return rec
        # 2b. unlock: result = IUnlockCallback(msg.sender).unlockCallback(data) (src/PoolManager.sol:110) ABI-decodes the return data as
        # bytes; return data shorter than an offset word plus a length word, or an offset or length past its end, reverts with no data
        if rec['call'] == 'unlock' and kids and not kids[0].get('error') and out in ('0x', ''):
            rb = bytes.fromhex((kids[0].get('output') or '0x')[2:])
            off = int.from_bytes(rb[:32], 'big') if len(rb) >= 32 else None
            bad_ret = off is None or off + 32 > len(rb) or off + 32 + int.from_bytes(rb[off:off + 32], 'big') > len(rb)
            if bad_ret:
                rec['class'] = 'source'; rec['why'] = 'callback returned %d bytes, which do not decode as bytes (src/PoolManager.sol:110)' % len(rb); return rec
        # 3. no such function
        if M.S.get((f.get('input') or '')[2:10]) is None and out in ('0x', ''):
            rec['class'] = 'source'; rec['why'] = 'selector not implemented, no fallback'; return rec
        # 4. source revert predicted by the model
        ok = False
        if pred and name and pred.split(':')[0] == name: ok = True
        if pred in ('underflow', 'overflow', 'int128 overflow') and sel == '0x4e487b71' and int(out[10:] or '0', 16) == 0x11: ok = True
        if pred in ('non-payable with value', 'bad bool', 'bad uint24') and out in ('0x', ''): ok = True
        if pred == 'UNAUTHORIZED' and sel == '0x08c379a0': ok = True
        if pred == 'SafeCastOverflow' and sel == '0x93dafdf1': ok = True
        rec['class'] = 'source' if ok else ('oog' if oog(f) else 'unexplained')
        rec['why'] = 'model raises %s' % pred if ok else 'model says %s, chain returned %s' % (pred, name or out[:10])
        return rec

def deepest(c):
    for k in c.get('calls', []) or []:
        if k.get('error') and (k.get('output') or '') == (c.get('output') or ''): return deepest(k)
    return {'to': c.get('to'), 'input4': (c.get('input') or '')[:10], 'error': c.get('error'), 'output': (c.get('output') or '')[:138]}

def pm_frames(f, acc):
    if (f.get('to') or '').lower() == PM: acc.append(f)
    for c in f.get('calls', []) or []: pm_frames(c, acc)
    return acc

tot = collections.Counter(); groups = collections.Counter(); recs = open(HERE + '/../results/replay-%d%s-records.jsonl' % (cid, TAG), 'w')
mmk = collections.Counter(); sels = collections.Counter(); native = collections.Counter()
for fn in sorted(glob.glob(D + '/tx/*.json.gz')):
    r = json.load(gzip.open(fn)); kind = r.get('kind', 'c23success'); tot[kind] += 1
    pre = (r.get('pre') or {}); pre = pre.get(next((k for k in pre if k.lower() == PM), ''), {})
    if not r.get('pre'): tot[kind + '-noPrestate'] += 1
    m = FModel(PM, pre.get('storage'), I(pre.get('balance')))
    err = None
    try:
        m.frame(r['call'])
        if kind in ('logfree', 'c23success') and r.get('diff'):
            dpre = next((v for k, v in r['diff']['pre'].items() if k.lower() == PM), {}); dpost = next((v for k, v in r['diff']['post'].items() if k.lower() == PM), {})
            m.finish(dpre, dpost)
            b0, b1 = m.bal_mined; exp1 = m.native['settle'] - m.native['take'] - m.native['collect']; exp2 = m.native['in_frames'] - m.native['out_frames']
            native['checked'] += 1
            if b1 != b0: native['moved'] += 1
            if b1 - b0 != exp1 or b1 - b0 != exp2: native['mismatch'] += 1; m.mis('native', diffPre=b0, diffPost=b1, settleMinusTake=exp1, valueFrames=exp2, flows=m.native)
    except Exception as e:
        err = traceback.format_exc()[-500:]; tot['exception'] += 1
    for f in pm_frames(r['call'], []): sels[(kind, M.S.get((f.get('input') or '')[2:10]) or (f.get('input') or '')[:10], bool(f.get('error')))] += 1
    tot[kind + '-wordsCompared'] += m.words_compared; tot[kind + '-logsClearedByTracer'] += m.logs_cleared
    root_err = r['call'].get('error')
    if kind == 'failed':
        if not m.cls: groups[('failed', 'no PoolManager frame failed', '-', 'top:' + str(root_err)[:40], 'every PoolManager frame returned; the transaction failed outside it')] += 1
    for c in m.cls:
        groups[(kind, c['class'], c['call'] or c['pmSelector'], c['decoded'] or c['output'][:10], c['why'][:70])] += 1
    real = list(m.mm)  # includes model-reverted: a frame that succeeded on chain for which the model raises a source revert (task 4a)
    for x in real: mmk[(kind, x['kind'])] += 1
    if real or err or any(c['class'] == 'unexplained' for c in m.cls) or m.cls:
        recs.write(json.dumps({'hash': r['hash'], 'block': r['block'], 'kind': kind, 'status': r.get('status'), 'url': r.get('url'), 'rootError': root_err,
                               'classified': m.cls, 'mismatches': real, 'exception': err, 'unread': len(m.unread), 'actions': m.actions[:40]}) + '\n')
    if m.unread: tot[kind + '-unreadSlots'] += 1
summ = {'chainId': cid, 'totals': dict(tot), 'native': dict(native),
        'classes': [{'kind': k[0], 'class': k[1], 'call': k[2], 'revert': k[3], 'why': k[4] if len(k) > 4 else '', 'frames': n} for k, n in groups.most_common()],
        'mismatchKinds': {'%s:%s' % k: n for k, n in mmk.items()},
        'pmFrames': {'%s:%s:%s' % (k[0], k[1], 'failed' if k[2] else 'ok'): n for k, n in sels.most_common()}}
json.dump(summ, open(HERE + '/../results/replay-%d%s.json' % (cid, TAG), 'w'), indent=1)
print(json.dumps(summ, indent=0)[:3500])
