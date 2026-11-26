"""L-1126 with the cycle 27 driver (src/Seq27.sol, build/seq27.json): the cycle 26 sequences, unchanged in what they
ask of the PoolManager, with step outputs kept in transient storage and the second CREATE2 of sequence e bounded.
Read-only: eth_call with state overrides. Setup steps of a and b may be run in the reference interpreter first and
their storage handed over as stateDiff (see l1126.py); the reference is then run from the same storage.
Usage: python3 -I run27.py <outdir> <chainId> <rpc url> [names...]   (names: a64 a512 b c c2 d300 e)"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import l1126 as T  # noqa: E402
S = T.S
S.B = json.load(open(os.path.join(HERE, 'build', 'seq27.json')))
P = T.P
from evm import rpc  # noqa: E402


def setpm(pm, url):
    T.PM = pm; T.URL = url


def run_split(name, prefix, body, tag):
    """Run body after prefix: prefix in the reference, body on chain in as few calls as fit."""
    out = []
    start = 0
    while start < len(body):
        n = len(body) - start
        while True:
            st = {}
            if prefix or start:
                ok, _, st = T.ref_run(prefix + body[:start]); st = {k: v for k, v in st.items() if v}
            part = body[start:start + n]
            okr, ref, _ = T.ref_run(part, st)
            got = T.chain(part, st, trace=True)
            time.sleep(1)
            okall = 'steps' in got and all(s['ok'] == 1 for s in got['steps']) and (not isinstance(ref, list) or all(s['ok'] == 1 for s in ref))
            res = T.cmp(got, ref)
            rec = {'seq': name, 'first': start, 'n': n, 'result': res, 'allStepsOk': okall,
                   'words': sum(len(s.get('w', [])) for s in got.get('steps', [])), **{k: v for k, v in got.items() if k != 'steps'}}
            if res != 'match':
                rec['got'] = got.get('steps'); rec['ref'] = ref
            print(tag, {k: v for k, v in rec.items() if k not in ('got', 'ref')}, flush=True)
            if res == 'match' and okall or n == 1:
                out.append(rec); start += n; break
            n = max(1, n // 2)
    return out


def main():
    od, cid, url = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    names = sys.argv[4:] or ['a64', 'b', 'c', 'c2', 'd300', 'e', 'a512']
    n = {x['chainId']: x for x in json.load(open(os.path.join(S.NR, 'state', 'networks.json')))['networks']}[cid]
    setpm(int(n['poolManager'], 16), url)
    salt = S.mine_salt()
    seqs = S.sequences(salt)
    path = os.path.join(od, f'run27-{cid}.json')
    rec = json.load(open(path)) if os.path.exists(path) else {'chainId': cid, 'rpc': url, 'salt': salt, 'seqs': {}}
    for nm in names:
        st = seqs[nm]
        if nm.startswith('a'):
            r = run_split(nm, st[:2], st[2:], cid)
        elif nm == 'e':
            got = T.chain(st, {}, trace=True)
            w = got.get('steps', [{}])[0]
            r = [{'seq': 'e', 'result': ('match' if w.get('ok') == 1 and S_e_expect(w['w']) else 'MISMATCH'), 'e': w,
                  **{k: v for k, v in got.items() if k != 'steps'}}]
            print(cid, r[0], flush=True)
        else:
            r = run_split(nm, [], st, cid)
        rec['seqs'][nm] = r
        json.dump(rec, open(path, 'w'), indent=1)


def S_e_expect(w):
    v = [int(x, 16) for x in w]
    # [h1, codehash, delta, markA, killOk, codeLenAfterKill, h2, codehashAfter, delta2, mark2]
    return len(v) == 10 and v[3] == 0xA and v[6] == 0 and v[9] == 0xA and v[5] > 0 and v[7] == v[1]


if __name__ == '__main__':
    main()
