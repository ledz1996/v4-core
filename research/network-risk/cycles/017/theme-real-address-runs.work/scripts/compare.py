"""Cycle 17, unit theme-real-address-runs, task 1: compare the real-address runs.

For each set and network: the record of every script at the network's real PoolManager address against
  (a) the record of the same script at Ethereum's real address,
  (b) the stored fresh-address result (opcodes/pmdiff.json, pmdiff2.json, pmdiff6.json: Ethereum's hash, and for the
      network the hash equals it unless the script index is listed as different there),
  (c) for sets 2 and 6, Ethereum's fresh-address record rerun in this cycle (raw/runs/s?-fresh-1.json.gz), call by call.
Before comparing, the 20 bytes of the PoolManager address are replaced by a marker in each record, so that two
networks with different PoolManager addresses can be compared. Every difference is reported with the first
differing call, its kind, and both sides' success flag, return length and first bytes.

Usage: python3 compare.py <out.json>
"""
import sys, os, json, gzip, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
import pmdiff as P  # noqa
import pmdiff3 as R  # noqa

RUNS = os.path.join(HERE, '..', 'raw', 'runs')
OPC = os.path.join(TOOLS, '..', '..', 'opcodes')
NWS = json.load(open(os.path.join(TOOLS, '..', '..', 'state', 'networks.json')))['networks']
STORED = {'1': 'pmdiff.json', '2': 'pmdiff2.json', '6': 'pmdiff6.json'}
MARK = b'\xee' * 20


def load(s, mode, cid):
    f = os.path.join(RUNS, f's{s}-{mode}-{cid}.json.gz')
    return json.load(gzip.open(f, 'rt')) if os.path.exists(f) else None


def raw(r): return None if r.startswith('ERR') else bytes.fromhex(r[2:])


def calls(s, kind_or_name, b, locked):
    if b is None: return None
    if s == '6' and not locked:
        try: b = R.unwrap(b)
        except Exception: return [('unparsed', b.hex()[:200])]  # noqa
    return P.parse(b)


def norm(b, pm):
    return None if b is None else b.replace(bytes.fromhex(pm[2:]), MARK)


def first_diff(ca, cb):
    if ca is None or cb is None: return {'index': None, 'note': 'one side has no record'}
    for i, (x, y) in enumerate(zip(ca, cb)):
        if x != y:
            return {'index': i, 'a': [x[0], len(x[1]), x[1][:68].hex()], 'b': [y[0], len(y[1]), y[1][:68].hex()]}
    return {'index': min(len(ca), len(cb)), 'note': f'lengths {len(ca)} and {len(cb)}'}


def main(outp):
    out = {}
    for s in ('1', '2', '6'):
        st = json.load(open(os.path.join(OPC, STORED[s])))
        refh = st['referenceHashes']; sdiff = {r['chainId']: set(r['different']) for r in st['results']}
        E = load(s, 'real', 1); Ef = load(s, 'fresh', 1)
        kinds = E['kinds']
        locked = [False] * len(kinds)
        if s == '6':
            import pmdiff6 as S6  # noqa
            locked = [d[:1] == b'\xff' for _, d in S6.scripts()]
        Er = [raw(x) for x in E['results']]; En = [norm(x, E['pm']) for x in Er]
        sec = {'ethereumRealVsStoredFresh': None, 'networks': {}}
        # Ethereum real against the stored fresh hash (on Ethereum, or the reference interpreter for set 6)
        eh = [hashlib.sha256(x).hexdigest() if x is not None else 'ERR' for x in Er]
        neq = [i for i, (a, b) in enumerate(zip(eh, refh)) if a != b and b != 'heavy']
        detail = {}
        for i in neq:
            fr = raw(Ef['results'][i]) if Ef else None
            detail[str(i)] = {'name': kinds[i] if s == '6' else None,
                              'vsEthereumFreshRerun': first_diff(calls(s, None, Er[i], locked[i]), calls(s, None, fr, locked[i])) if fr is not None else None,
                              'freshRerunEqualsStored': (hashlib.sha256(fr).hexdigest() == refh[i]) if fr is not None else None}
            if detail[str(i)]['vsEthereumFreshRerun'] and detail[str(i)]['vsEthereumFreshRerun'].get('index') is not None and s != '1':
                k = detail[str(i)]['vsEthereumFreshRerun']['index']
                detail[str(i)]['callKind'] = (kinds[i][k] if s != '6' else None)
        sec['ethereumRealVsStoredFresh'] = {'equal': len(Er) - len(neq) - sum(1 for b in refh if b == 'heavy'), 'heavySkipped': sum(1 for b in refh if b == 'heavy'),
                                            'different': neq, 'detail': detail}
        for nw in NWS:
            cid = nw['chainId']
            if cid == 1: continue
            X = load(s, 'real', cid)
            if X is None: sec['networks'][str(cid)] = 'missing'; continue
            Xr = [raw(x) for x in X['results']]; Xn = [norm(x, X['pm']) for x in Xr]
            errs = [i for i, x in enumerate(X['results']) if x.startswith('ERR')]
            dif = [i for i in range(len(Xn)) if Xn[i] != En[i] and Xn[i] is not None and En[i] is not None]
            xh = [hashlib.sha256(x).hexdigest() if x is not None else 'ERR' for x in Xr]
            # stored fresh result of this network: the reference hash unless the index is listed as different
            vs_fresh = [i for i in range(len(xh)) if refh[i] != 'heavy' and i not in sdiff.get(cid, set()) and xh[i] != refh[i]]
            d = {}
            for i in dif:
                fd = first_diff(calls(s, None, Xn[i], locked[i]), calls(s, None, En[i], locked[i]))
                k = fd.get('index')
                d[str(i)] = dict(fd, kind=(kinds[i][k] if s != '6' and k is not None and k < len(kinds[i]) else None),
                                 name=(kinds[i] if s == '6' else None), storedFreshDifferent=i in sdiff.get(cid, set()))
            sec['networks'][str(cid)] = {'name': nw['name'], 'pm': X['pm'], 'pmCodeSha256': X['pmCodeSha256'], 'pmCodeLen': X['pmCodeLen'],
                                         'clientVersion': X['clientVersion'], 'block': X['blockBefore'],
                                         'equalToEthereumReal': len(Xn) - len(dif) - len(errs), 'differentFromEthereumReal': dif,
                                         'errors': {str(i): X['results'][i][:200] for i in errs},
                                         'differentFromStoredFresh': vs_fresh,
                                         'storedFreshDifferent': sorted(sdiff.get(cid, set())), 'detail': d}
        out['set' + s] = sec
    json.dump(out, open(outp, 'w'), indent=1)
    for s in ('1', '2', '6'):
        sec = out['set' + s]
        print('set', s, 'Ethereum real vs stored fresh: different', sec['ethereumRealVsStoredFresh']['different'])
        for cid, v in sec['networks'].items():
            if isinstance(v, str): print('  ', cid, v); continue
            print(f"   {cid:>8} {v['name'][:14]:14} eqEth {v['equalToEthereumReal']:4} diffEth {v['differentFromEthereumReal']} errs {list(v['errors'])} diffStoredFresh {v['differentFromStoredFresh']} storedFreshDiff {v['storedFreshDifferent']}")


if __name__ == '__main__':
    main(sys.argv[1])
