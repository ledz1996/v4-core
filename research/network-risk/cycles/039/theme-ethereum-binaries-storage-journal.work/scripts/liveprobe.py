"""Cycle 39, task 1 and 4 live part: the nested-frame storage sequences of seqs.py (seed 39_1346_01, the first N with
no filler prefix) compiled to bytecode and sent by eth_call with state overrides (read-only) to one public endpoint
per client release, each batch bracketed by web3_clientVersion. The same codes run in tools/opdiff/pyevm.py.

Compilation: the outer frame is the code at PROBE; each inner frame of the sequence is a separate code at its own
address entered by DELEGATECALL, so every frame acts on PROBE's storage and transient storage as the PoolManager's
reentrant frames act on the PoolManager's. A frame writes each read (TLOAD/SLOAD) to its memory, and after each
child it records the child's success flag and copies the child's returned words; a frame that the sequence reverts
ends with REVERT carrying its words, so reads inside reverted frames are compared too. The persistent slots start at
the sequence's initial values through stateDiff. Addresses outside PROBE (TOKEN, HOOK) are folded onto PROBE's
storage, so the settle shape's token balance slot is a slot of PROBE here.
usage: python3 -I liveprobe.py <out.json> <n> <url> [url ...]"""
import json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import seqs as S
import pyevm as PE
from evm import assemble, rpc, _ctx

PROBE = 0x00000000000000000000000000000000000b0be1
FRAME0 = 0x00000000000000000000000000000000000f0000


def tree(seq):
    """nested list: items are steps or ('frame', kind, items)"""
    root = []; stack = [root]
    for st in seq:
        if st[0] == 'snap':
            fr = ['frame', None, []]; stack[-1].append(fr); stack.append(fr[2])
        elif st[0] in ('rev', 'commit'):
            stack.pop(); stack[-1][-1][1] = st[0]
        else:
            stack[-1].append(st)
    return root


def compile_seq(seq):
    codes = {}; nxt = [FRAME0]

    def words(items):
        n = 0
        for it in items:
            if it[0] == 'frame': n += 1 + words(it[2])
            elif it[0] in ('tld', 'sld'): n += 1
        return n

    def frame(items, kind):
        prog = []; off = 0
        for it in items:
            if it[0] == 'frame':
                addr = nxt[0]; nxt[0] += 1
                codes[addr] = frame(it[2], it[1])
                n = words(it[2])
                prog += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', addr), 'GAS', 'DELEGATECALL',
                         ('PUSH', off), 'MSTORE']; off += 32
                if n:
                    prog += [('PUSH', 32 * n), ('PUSH', 0), ('PUSH', off), 'RETURNDATACOPY']; off += 32 * n
            elif it[0] == 'tst': prog += [('PUSH', it[3]), ('PUSH', it[2]), 'TSTORE']
            elif it[0] == 'sst': prog += [('PUSH', it[3]), ('PUSH', it[2]), 'SSTORE']
            elif it[0] == 'tld': prog += [('PUSH', it[2]), 'TLOAD', ('PUSH', off), 'MSTORE']; off += 32
            elif it[0] == 'sld': prog += [('PUSH', it[2]), 'SLOAD', ('PUSH', off), 'MSTORE']; off += 32
        prog += [('PUSH', off), ('PUSH', 0), 'REVERT' if kind == 'rev' else 'RETURN']
        return assemble(prog)

    items = tree(seq)
    codes[PROBE] = frame(items, 'commit')
    return codes


def fold(seq, db):
    seq2 = [tuple([st[0], PROBE] + list(st[2:])) if len(st) > 1 else st for st in seq]
    st = {}
    for (a, s), v in db.items():
        if a == S.PM: st[s] = v
    for (a, s), v in db.items():
        if a != S.PM: st.setdefault(s, v)
    return seq2, st


def ref(codes, storage):
    w = PE.World(codes)
    w.storage = {(PROBE, s): v for s, v in storage.items()}
    ok, r = w.call(1, PROBE, 0, b'', False, 1)
    return ok, r


def ask(url, codes, storage):
    ov = {'0x' + a.to_bytes(20, 'big').hex(): {'code': '0x' + c.hex()} for a, c in codes.items()}
    ov['0x' + PROBE.to_bytes(20, 'big').hex()]['stateDiff'] = {'0x' + s.to_bytes(32, 'big').hex(): '0x' + v.to_bytes(32, 'big').hex() for s, v in storage.items()}
    tx = {'from': '0x' + '00' * 19 + '01', 'to': '0x' + PROBE.to_bytes(20, 'big').hex(), 'data': '0x', 'gas': hex(20_000_000)}
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [tx, 'latest', ov]}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60, context=_ctx) as r:
                j = json.load(r)
            if 'error' in j: return False, json.dumps(j['error'])[:300]
            return True, bytes.fromhex(j['result'][2:])
        except Exception as e:
            err = str(e)[:200]; time.sleep(2 + 3 * k)
    return False, 'transport: ' + err


if __name__ == '__main__':
    OUT, N, URLS = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    cases = []
    for seq, db in S.sequences(4 * N):
        if any(st[0] in ('tst', 'sst') and st[2] not in S.TSLOTS + S.PSLOTS + [S.TOKBAL] for st in seq): continue  # no filler
        cases.append((seq, db))
        if len(cases) >= N: break
    out = {'seed': S.SEED, 'cases': len(cases), 'results': []}
    for url in URLS:
        r = {'rpc': url, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        try: r['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [], 30)
        except Exception as e: r['clientVersionBefore'] = 'ERR ' + str(e)[:200]
        ran = 0; bad = []; errs = []; words = 0
        for i, (seq, db) in enumerate(cases):
            s2, storage = fold(seq, db)
            codes = compile_seq(s2)
            ok1, r1 = ref(codes, storage)
            ok2, r2 = ask(url, codes, storage)
            if not ok2 and isinstance(r2, str):
                errs.append([i, r2])
                if len(errs) > 20: break
                continue
            ran += 1; words += len(r1) // 32
            if (ok1, r1) != (True, r2):
                bad.append({'case': i, 'steps': [[S.hx(v) for v in st] for st in s2], 'storage': {hex(k): hex(v) for k, v in storage.items()},
                            'ref': r1.hex(), 'node': r2.hex()})
        try: r['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [], 30)
        except Exception as e: r['clientVersionAfter'] = 'ERR ' + str(e)[:200]
        r.update({'ran': ran, 'wordsCompared': words, 'mismatchCount': len(bad), 'mismatches': bad, 'errors': errs})
        print(url, r['clientVersionBefore'], r['clientVersionAfter'], 'ran', ran, 'words', words, 'mismatches', len(bad), 'errors', len(errs), errs[:2], flush=True)
        out['results'].append(r)
    json.dump(out, open(OUT, 'w'), indent=1)
