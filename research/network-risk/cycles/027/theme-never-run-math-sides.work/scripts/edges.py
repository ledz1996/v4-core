"""Cycle 27, theme-never-run-math-sides, Task 3: operand edges reached by mined frames of closed producers.

Reruns every PoolManager frame of the transactions cycle 23 saved (cycles/023/theme-state-replay.work/raw/<cid>/tx,
prestate plus callTracer tree) through the cycle 24 counting interpreter (cycles/024/.../scripts/pyevm_cov.py, a copy of
tools/opdiff/pyevm.py) with the cycle 24 replay world (replaycov.PMWorld: outgoing calls answered from the recorded call
tree). Offline; no network access. At every arithmetic, shift, byte and comparison instruction of the build it classifies
the operands into edge classes and counts frames-steps per (pc, edge). Frame results are compared with the recorded
call tree as in cycle 24, so a count is only kept from a transaction whose PoolManager frames all reproduce.
usage: edges.py <cid> <shard> <nshards>  writes ../out/edges-<cid>-<shard>.json"""
import sys, os, json, gzip, glob, time
sys.setrecursionlimit(20000)
C24 = '/home/user/v4-core/research/network-risk/cycles/024/theme-producer-branch-coverage.work/scripts'
sys.path.insert(0, C24)
import replaycov as R
import pyevm_cov as P
from sites import sites
HERE = os.path.dirname(os.path.abspath(__file__))
M = (1 << 256) - 1
L64 = (1 << 64) - 1
OPS = {'MULMOD', 'ADDMOD', 'SAR', 'SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SDIV', 'SMOD', 'DIV', 'MOD', 'EXP', 'SLT', 'SGT',
       'LT', 'GT', 'MUL', 'ADD', 'SUB'}


def s(x): return x - (1 << 256) if x >> 255 else x


def limbs_borrow_all(a, b):
    br = 0; n = 0
    for i in range(4):
        ai = (a >> (64 * i)) & L64; bi = (b >> (64 * i)) & L64
        br = 1 if ai < bi + br else 0; n += br
    return n == 4


def limbs_carry_all(a, b):
    cr = 0; n = 0
    for i in range(4):
        ai = (a >> (64 * i)) & L64; bi = (b >> (64 * i)) & L64
        cr = 1 if ai + bi + cr > L64 else 0; n += cr
    return n == 4


def edges(op, st):
    a = st[-1]; b = st[-2]
    e = []
    if op == 'MULMOD':
        n = st[-3]; p = a * b
        if n == M: e.append('mod=not0')
        if n == 0: e.append('mod=0')
        if p >> 256: e.append('product>=2^256')
        if n == M and p >> 256: e.append('mod=not0&highword!=0')
        if n and n != M and p >> 256: e.append('wideproduct&mod<not0')
        if n and p % n == 0: e.append('rem=0')
        elif n: e.append('rem!=0')
        if n >> 128: e.append('mod>2^128')
    elif op == 'ADDMOD':
        n = st[-3]
        if a + b > M: e.append('sum>=2^256')
    elif op == 'SAR':
        if a == 255: e.append('shift=255&neg' if b >> 255 else 'shift=255&nonneg')
        elif a >= 256: e.append('shift>=256')
        elif b >> 255: e.append('neg')
    elif op == 'SIGNEXTEND':
        if a == 2: e.append('b=2&neg' if (b >> 23) & 1 else 'b=2&nonneg')
        if a < 31 and (b >> (8 * a + 8)): e.append('highbits-dirty')
    elif op == 'BYTE':
        if a == 31: e.append('index=31')
        if a >= 32: e.append('index>=32')
    elif op in ('SHL', 'SHR'):
        if a in (96, 128, 192): e.append('shift=%d' % a)
        if a >= 256: e.append('shift>=256')
        if op == 'SHL' and a < 256 and (b << a) >> 256: e.append('bitslost')
        if op == 'SHR' and a < 256 and b and (b >> a) == 0: e.append('result0-from-nonzero')
    elif op in ('SDIV', 'SMOD'):
        sa, sb = s(a), s(b)
        if sb == 0: e.append('div0')
        if sa < 0: e.append('numNeg')
        if sb < 0: e.append('denNeg')
        if sa < 0 and sb > 0 and sa % sb != 0: e.append('numNeg&inexact')
        if sa == -(1 << 255) and sb == -1: e.append('min/-1')
    elif op in ('DIV', 'MOD'):
        if b == 0: e.append('div0')
        elif b >> 128: e.append('div>2^128')
        if b and a < b: e.append('num<den')
        if b and b >> 192: e.append('div>2^192')
    elif op == 'EXP':
        if b == 0: e.append('exp0')
        if b >= 256: e.append('exp>=256')
    elif op == 'MUL':
        if (a * b) >> 256: e.append('wrap')
    elif op == 'SUB':
        if a < b: e.append('borrow')
        if limbs_borrow_all(a, b): e.append('borrow-all-4-limbs')
    elif op == 'ADD':
        if a + b > M: e.append('carry-out')
        if limbs_carry_all(a, b): e.append('carry-all-4-limbs')
    elif op in ('SLT', 'SGT', 'LT', 'GT'):
        if (a >> 255) != (b >> 255): e.append('opposite-sign')
        if a == b: e.append('equal')
        elif abs(a - b) == 1: e.append('adjacent')
    return e


def main():
    cid, shard, nsh = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    pm = R.NETS[cid]['poolManager'].lower(); pmi = int(pm, 16); code = R.code_for(pm)
    files = sorted(glob.glob('%s/%d/tx/*.json.gz' % (R.RAW, cid)))[shard::nsh]
    watch = {p: n for p, n, f, l, sn in sites() if n in OPS}
    CNT = {}; HIT = {}
    cur = {'hash': None}

    def cb(pc, op, st):
        HIT[pc] = HIT.get(pc, 0) + 1
        for ed in edges(watch[pc], st):
            k = (pc, ed); CNT[k] = CNT.get(k, 0) + 1
    tot = {'txs': 0, 'frames': 0, 'frameMismatch': 0, 'div': 0, 'setAside': 0, 'steps': 0}
    bad = []; t0 = time.time()
    for fn in files:
        rec = json.load(gzip.open(fn)); cur['hash'] = rec['hash']
        pre = next((v for k, v in rec['pre'].items() if k.lower() == pm), {})
        w = R.PMWorld({pmi: code}, {pmi: int(pre.get('balance', '0x0'), 16)})
        for k, v in (pre.get('storage') or {}).items(): w.storage[(pmi, int(k, 16))] = int(v, 16)
        w.pm = pmi; w.frames = []; w.stack = []; w.divs = []; w.forced = 0; w.max_steps = 50_000_000
        w.watch = set(watch); w.watch_addr = pmi; w.watch_cb = cb
        ct = rec['call']; tot['txs'] += 1
        try:
            if (ct.get('to') or '').lower() == pm:
                w.pending = ct; w.call(int(ct['from'], 16), pmi, int(ct.get('value') or '0x0', 16), bytes.fromhex(ct['input'][2:]), False, 0)
            else:
                w.replay_children(ct)
        except R.Div:
            tot['div'] += 1; bad.append({'hash': rec['hash'], 'kind': 'divergence', 'divs': w.divs[:3]}); continue
        except (NotImplementedError, TimeoutError) as ex:
            tot['setAside'] += 1; bad.append({'hash': rec['hash'], 'kind': 'setAside', 'err': str(ex)[:200]}); continue
        tot['steps'] += w.steps; tot['frames'] += len(w.frames)
        fm = [(nd, ok, ret) for nd, ok, ret, forced in w.frames if not forced and (ok != ('error' not in nd) or (ok and '0x' + ret.hex() != (nd.get('output') or '0x').lower()))]
        if fm:
            tot['frameMismatch'] += 1
            bad.append({'hash': rec['hash'], 'kind': 'frame', 'detail': [{'input': nd.get('input', '')[:200], 'ok': ok, 'ret': ret.hex()[:400], 'recErr': nd.get('error'), 'recOut': (nd.get('output') or '')[:402]} for nd, ok, ret in fm[:3]]})
    tot['secs'] = round(time.time() - t0, 1)
    out = {'chainId': cid, 'shard': shard, 'nshards': nsh, 'totals': tot, 'mismatches': bad,
           'hits': {str(k): v for k, v in HIT.items()}, 'edges': {'%d|%s' % k: v for k, v in CNT.items()}}
    json.dump(out, open('%s/../out/edges-%d-%d.json' % (HERE, cid, shard), 'w'))
    print(json.dumps(tot), flush=True)


if __name__ == '__main__':
    main()
