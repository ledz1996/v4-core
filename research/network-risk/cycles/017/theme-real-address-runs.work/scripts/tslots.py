"""Cycle 17, unit theme-real-address-runs, task 3.

At the real PoolManager address of each network, read the transient slots the source defines
(Lock.sol:8 IS_UNLOCKED_SLOT, NonzeroDeltaCount.sol:8-9 NONZERO_DELTA_COUNT_SLOT, CurrencyReserves.sol:11 RESERVES_OF_SLOT,
CurrencyReserves.sol:13 CURRENCY_SLOT, and the delta slots of CurrencyDelta for the driver) through exttload:

  A. a plain eth_call of exttload(bytes32[]) to the PoolManager, at 'latest' and at 'pending', from three senders
  B. inside one simulated call, with the pmdiff6 driver placed by override (the PoolManager is not overridden):
       outer frame, before unlock      -> all four must read 0
       inside the callback, first      -> unlocked 1, count 0, currency 0, reserves 0
       after sync(token double)        -> currency = token, reserves = its balance
       after mint(driver, T0, 5)       -> count 1, delta(driver, T0) = -5
       after burn(driver, T0, 5)       -> count 0, delta 0
       outer frame, after unlock       -> unlocked 0, count 0, currency still the token (sync is cleared only by settle)
  C. persistent slots 0 and 1 (owner, and the root of the protocolFeesAccrued mapping, which holds nothing) and extsload of the four constants as persistent slots,
     which must be 0 (the constants are transient slot names; a client that mixed the two spaces would show it).

Usage: python3 tslots.py <out.json> [chainId ...]
"""
import sys, os, json, time, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
from evm import rpc, keccak  # noqa

NWS = json.load(open(os.path.join(TOOLS, '..', '..', 'state', 'networks.json')))['networks']
SLOTS = {'unlocked': 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23,
         'count': 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b,
         'reserves': 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95,
         'currency': 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9}
for name, txt in (('unlocked', 'Unlocked'), ('count', 'NonzeroDeltaCount'), ('reserves', 'ReservesOf'), ('currency', 'Currency')):
    assert SLOTS[name] == int.from_bytes(keccak(txt.encode()), 'big') - 1
ORDER = ['unlocked', 'count', 'reserves', 'currency']


def w(x): return (x % (1 << 256)).to_bytes(32, 'big')


def sel(s): return keccak(s.encode())[:4]


EXTT_ARR = sel('exttload(bytes32[])')
EXTS_ARR = sel('extsload(bytes32[])')


def arr_call(selector, slots): return selector + w(0x20) + w(len(slots)) + b''.join(w(s) for s in slots)


def dec_arr(hexret):
    b = bytes.fromhex(hexret[2:]); n = int.from_bytes(b[32:64], 'big')
    return [int.from_bytes(b[64 + 32 * i:96 + 32 * i], 'big') for i in range(n)]


def per_net(nw):
    cid, url, pm = nw['chainId'], nw['rpc'], '0x' + nw['poolManager'][2:].lower()
    # the driver modules read the PoolManager address when imported, so each network runs in its own process (see main)
    import pmdiff as P
    P.PM = pm
    import pmdiff6 as S6
    PMI = int(pm, 16); DRV = S6.DRV; T0, T1 = S6.T0, S6.T1
    out = {'chainId': cid, 'name': nw['name'], 'pm': pm}

    def q(method, params):
        last = None
        for k in range(6):
            try: return rpc(url, method, params, timeout=90)
            except Exception as e:  # noqa
                last = 'ERR ' + str(e)[:200]; time.sleep(2 * (k + 1))
        return last

    out['block'] = q('eth_blockNumber', [])
    dslots = [int.from_bytes(keccak(w(DRV) + w(c)), 'big') for c in (T0, T1, 0)]
    allslots = [SLOTS[k] for k in ORDER] + dslots
    # A
    a = {}
    for tag in ('latest', 'pending'):
        for frm in ('0x0000000000000000000000000000000000000000', '0x000000000000000000000000000000000000dEaD', '0x' + DRV.to_bytes(20, 'big').hex()):
            r = q('eth_call', [{'from': frm, 'to': pm, 'data': '0x' + arr_call(EXTT_ARR, allslots).hex()}, tag])
            a[f'{tag} from {frm}'] = dec_arr(r) if r and not r.startswith('ERR') else r
    out['A'] = a
    # B
    ex4 = [S6.text(SLOTS[k]) for k in ORDER]
    inner = (ex4 + [S6.it(T1, S6.TSET + w(1000)), S6.it(PMI, S6.S['sync'] + w(T1))] + ex4 +
             [S6.it(PMI, S6.S['mint'] + w(DRV) + w(T0) + w(5)), S6.text(SLOTS['count']), S6.text(dslots[0]),
              S6.it(PMI, S6.S['burn'] + w(DRV) + w(T0) + w(5))] + ex4 + [S6.text(dslots[0])])
    inner_b = b''.join(inner) + S6.end(1)
    unlock_cd = S6.S['unlock'] + w(0x20) + w(len(inner_b)) + inner_b + bytes(-len(inner_b) % 32)
    outer = b'\xff' + b''.join(ex4 + [S6.it(PMI, unlock_cd)] + ex4) + S6.end(0)
    ov = S6.overrides(b''); del ov['0x' + PMI.to_bytes(20, 'big').hex()]
    r = q('eth_call', [{'to': '0x' + DRV.to_bytes(20, 'big').hex(), 'data': '0x' + outer.hex(), 'gas': hex(5_000_000)}, 'latest', ov])
    b = {'raw': r}
    if r and not r.startswith('ERR'):
        recs = P.parse(bytes.fromhex(r[2:]))
        word = lambda rec: int.from_bytes(rec[1][:32], 'big') if rec[0] and len(rec[1]) == 32 else ('fail', rec[1].hex())
        b['before'] = dict(zip(ORDER, [word(x) for x in recs[0:4]]))
        b['unlockOk'] = recs[4][0]
        b['after'] = dict(zip(ORDER, [word(x) for x in recs[5:9]]))
        if recs[4][0]:
            ib = recs[4][1]; n = int.from_bytes(ib[32:64], 'big'); innerrec = ib[64:64 + n]
            ir = P.parse(innerrec)
            b['innerFirst'] = dict(zip(ORDER, [word(x) for x in ir[0:4]]))
            b['syncCalls'] = [x[0] for x in ir[4:6]]
            b['afterSync'] = dict(zip(ORDER, [word(x) for x in ir[6:10]]))
            b['mintOk'] = ir[10][0]; b['countAfterMint'] = word(ir[11]); b['deltaAfterMint'] = word(ir[12])
            b['burnOk'] = ir[13][0]
            b['afterBurn'] = dict(zip(ORDER, [word(x) for x in ir[14:18]])); b['deltaAfterBurn'] = word(ir[18])
        exp = {'before': [0, 0, 0, 0], 'innerFirst': [1, 0, 0, 0], 'afterSync': [1, 0, 1000, T1], 'afterBurn': [1, 0, 1000, T1], 'after': [0, 0, 1000, T1]}
        b['ok'] = all(b.get(k) and [b[k][x] for x in ORDER] == v for k, v in exp.items()) and b.get('countAfterMint') == 1 and \
            b.get('deltaAfterMint') == (1 << 256) - 5 and b.get('deltaAfterBurn') == 0 and b.get('unlockOk') == 1
    out['B'] = b
    # C
    r = q('eth_call', [{'to': pm, 'data': '0x' + arr_call(EXTS_ARR, [0, 1] + [SLOTS[k] for k in ORDER]).hex()}, 'latest'])
    out['C'] = dec_arr(r) if r and not r.startswith('ERR') else r
    out['A_ok'] = all(isinstance(v, list) and v == [0] * len(allslots) for v in a.values())
    out['C_ok'] = isinstance(out['C'], list) and out['C'][2:] == [0, 0, 0, 0]
    return out


if __name__ == '__main__':
    outp = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    if len(only) == 1:
        nw = [n for n in NWS if n['chainId'] in only][0]
        json.dump(per_net(nw), open(outp, 'w'), indent=1); sys.exit(0)
    import subprocess
    nets = [n for n in NWS if not only or n['chainId'] in only]
    tmp = [outp + f'.{n["chainId"]}' for n in nets]
    procs = [subprocess.Popen([sys.executable, __file__, t, str(n['chainId'])]) for n, t in zip(nets, tmp)]
    for p in procs: p.wait()
    res = []
    for t in tmp:
        try: res.append(json.load(open(t))); os.remove(t)
        except Exception as e: res.append({'file': t, 'error': str(e)})  # noqa
    json.dump(res, open(outp, 'w'), indent=1)
    for r in res:
        print(r.get('chainId'), r.get('name'), 'A', r.get('A_ok'), 'B', r.get('B', {}).get('ok'), 'C', r.get('C_ok'), r.get('C', '')[:2] if isinstance(r.get('C'), list) else r.get('C'))
