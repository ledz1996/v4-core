"""Compare every returned word of every network with the reference interpreter (pyevm.py, run on exactly the step list
of each eth_call, so split sequences get their own reference) and with Ethereum. Sequence e has no reference run; it is
compared with Ethereum and with the EIP-6780 expectation (second CREATE2 fails, the old code still runs).
Usage: python3 -I compare.py <outdir> <out.json>"""
import sys, os, json, glob, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
import pyevm as P
od = sys.argv[1]
salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
SEQ = S.sequences(salt)
cache_p = os.path.join(od, 'refcache.json')
cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}


def ref(steps):
    h = hashlib.sha256(b''.join(steps)).hexdigest()
    if h not in cache:
        wd = P.World(S.codes(0x000000000004444c5dc75cB358380D2e3dE08A90))
        ok, ret = wd.call(S.EOA, S.D, 0, S.enc_run(steps), False, 0)
        cache[h] = S.dec_run(ret) if ok else {'topFail': ret.hex()}
    return cache[h]


def parts_of(name, calls):
    parts = [SEQ[name]]; out = []
    for c in calls:
        st = parts.pop(0)
        if c.get('split'):
            h = len(st) // 2; parts[:0] = [st[:h], st[:2] + st[h:]]
        else:
            out.append((c, st))
    return out


def e_expect(w):
    v = [int(x, 16) for x in w]
    # [h1, codehash, delta, markA, killOk, codeLenAfterKill, h2, codehashAfter, delta2, mark2]
    return v[3] == 0xA and v[6] == 0 and v[9] == 0xA and v[5] > 0 and v[7] == v[1]


rows = []; mism = []
eth = {}
for f in sorted(glob.glob(os.path.join(od, 'chain-*.json'))):
    r = json.load(open(f))
    for nm, v in r['seqs'].items():
        for c, st in parts_of(nm, v['calls']):
            row = {'chainId': r['chainId'], 'endpoint': r['rpc'], 'seq': nm, 'nsteps': len(st), 'block': c.get('block'),
                   'clientBefore': c.get('clientBefore'), 'clientAfter': c.get('clientAfter'), 'gas': c.get('gas')}
            if 'error' in c:
                row['result'] = 'refused' if c.get('refusedByEndpoint') else 'error'; row['error'] = c['error'][:200]
            elif nm == 'e':
                ok = c['steps'][0]['ok'] == 1 and e_expect(c['steps'][0]['w'])
                row['result'] = 'match' if ok else 'MISMATCH'; row['words'] = len(c['steps'][0].get('w', []))
                row['e'] = c['steps'][0]
                if not ok: mism.append(dict(row, got=c['steps']))
            else:
                rf = ref(st)
                nw = sum(len(s.get('w', [])) for s in c['steps'])
                row['words'] = nw
                if c['steps'] == rf:
                    row['result'] = 'match'
                else:
                    row['result'] = 'MISMATCH'; mism.append(dict(row, got=c['steps'], ref=rf))
            rows.append(row)
json.dump(cache, open(cache_p, 'w'))
summ = {}
for x in rows:
    k = x['chainId']; s = summ.setdefault(k, {'calls': 0, 'match': 0, 'mismatch': 0, 'error': 0, 'refused': 0, 'words': 0, 'clients': set(), 'endpoints': set()})
    s['calls'] += 1; s['words'] += x.get('words', 0); s['endpoints'].add(x['endpoint'])
    s[{'match': 'match', 'MISMATCH': 'mismatch', 'error': 'error', 'refused': 'refused'}[x['result']]] += 1
    for cv in (x['clientBefore'], x['clientAfter']):
        if cv and not cv.startswith('error'): s['clients'].add(cv)
for k, s in summ.items(): s['clients'] = sorted(s['clients']); s['endpoints'] = sorted(s['endpoints'])
for k in sorted(summ): print(k, {a: b for a, b in summ[k].items() if a != 'clients'}, summ[k]['clients'][:4])
json.dump({'summary': summ, 'rows': rows, 'mismatches': mism}, open(sys.argv[2], 'w'), indent=1, default=list)
print('mismatches', len(mism))
