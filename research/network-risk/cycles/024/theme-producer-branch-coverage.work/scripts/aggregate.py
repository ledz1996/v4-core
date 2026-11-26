"""Merge shards of replaycov.py: per network, each JUMPI side count with its source line; operand ranges of watched sites.
usage: aggregate.py <cid>...   writes ../out/<cid>/branches.json and ../out/jumps-summary.json"""
import sys, json, glob, os
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap as S
HERE = os.path.dirname(os.path.abspath(__file__))
JM = json.load(open('/home/user/v4-core/research/network-risk/opcodes/jumpmap.json'))
unreach = {e['pc']: e for e in JM['oneSided']}; never = {e['pc']: e for e in JM['neverReached']}
jumpis = [p for p in S.starts[:S.NCODE] if S.code[p] == 0x57]
def load(cid):
    br = {}; W = {}; tot = {}; mm = []; pertx = {}
    for f in sorted(glob.glob('%s/../out/%d/shard*.json' % (HERE, cid))):
        d = json.load(open(f))
        for k, v in d['branches'].items(): br[k] = br.get(k, 0) + v
        for k, v in d['totals'].items():
            if isinstance(v, (int, float)): tot[k] = tot.get(k, 0) + v
        mm += d['mismatches']; pertx.update(d['pertx'])
        for pc, (op, n, ops) in d['watch'].items():
            if pc not in W: W[pc] = [op, n, ops]
            else:
                e = W[pc]; e[1] += n
                for a, b in zip(e[2], ops):
                    a[0] = min(a[0], b[0]); a[1] = max(a[1], b[1]); a[2] = min(a[2], b[2]); a[3] = max(a[3], b[3]); a[4] += b[4]; a[5] = sorted(set(a[5]) | set(b[5]))
    return br, W, tot, mm, pertx
if __name__ == '__main__':
    summ = {}
    for cid in map(int, sys.argv[1:]):
        br, W, tot, mm, pertx = load(cid)
        rows = []; both = one = nev = 0
        for p in jumpis:
            t = br.get('%d:1' % p, 0); f = br.get('%d:0' % p, 0)
            st = 'both' if t and f else ('one' if t or f else 'never')
            both += st == 'both'; one += st == 'one'; nev += st == 'never'
            l = S.loc(p)
            rows.append({'pc': p, 'taken': t, 'fallthrough': f, 'status': st, 'file': l['file'], 'line': l.get('line'), 'snippet': l.get('snippet', '')[:120],
                         'cycle12': 'unreachable side: ' + unreach[p]['why'][:160] if p in unreach else ('never reached by tests: ' + never[p]['why'][:160] if p in never else '')})
        out = {'chainId': cid, 'totals': tot, 'jumpi': len(jumpis), 'both': both, 'oneSide': one, 'never': nev, 'rows': rows, 'watch': W, 'mismatches': mm}
        json.dump(out, open('%s/../out/%d/branches.json' % (HERE, cid), 'w'), indent=0)
        summ[cid] = {'txs': tot.get('txs'), 'frames': tot.get('frames'), 'steps': tot.get('steps'), 'mismatchRecords': len(mm), 'jumpi': len(jumpis), 'both': both, 'oneSide': one, 'never': nev}
        print(cid, summ[cid])
    json.dump(summ, open('%s/../out/jumps-summary.json' % HERE, 'w'), indent=1)
