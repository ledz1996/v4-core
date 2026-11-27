"""Cycle 37, Task 3: Arc's native value hook (check_blocklist_and_create_log, crates/evm/src/evm.rs 516-605 at v0.8.6)
inside a call frame that commits or reverts, probed read-only by eth_simulateV1 (logs) and eth_call, with code,
balance and storage overrides only. No transaction is sent. Bracketed by web3_clientVersion.

F0 (0xc0de0000) writes the PoolManager's lock and nonzero-delta-count transient words and a storage word, reads the
native balances of F0, F1 and T and the 0x3600 ERC-20 face balanceOf(T), then DELEGATECALLs F1, which runs on F0's account: it changes the
same transient words, writes the same storage word, CALLs T with value V and records the call flag, then REVERTs or RETURNs.
F0 then reads everything again and returns one record. T is a plain contract (accepted transfer) or an address
whose NativeCoinControl blocklist word is overridden to 1 (rejected transfer).
usage: python3 -I arc_hook_probe.py <url> <out.json>"""
import json, sys, time, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak

URL, OUT = sys.argv[1], sys.argv[2]
F0, F1, T_OK, T_BL = 0xc0de0000, 0xc0de0001, 0xc0de0002, 0xb10c0000000000000000000000000000000000b1
FROM = 0xca11e4
FACE = 0x3600000000000000000000000000000000000000
NCC = 0x1800000000000000000000000000000000000001
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23   # src/libraries/Lock.sol
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b   # src/libraries/NonzeroDeltaCount.sol
V = 10 ** 15


def kw(*ws): return int.from_bytes(keccak(b''.join(w.to_bytes(32, 'big') for w in ws)), 'big')


def push(v):
    b = v.to_bytes(max(1, (v.bit_length() + 7) // 8), 'big'); return bytes([0x5f + len(b)]) + b if v else b'\x5f'


def f1_code(target, revert):
    c = bytearray()
    c += push(9) + push(LOCK) + b'\x5d' + push(3) + push(NZDC) + b'\x5d'          # TSTORE lock=9, count=3
    c += push(6) + push(1) + b'\x55'                                               # SSTORE slot1 = 6
    # CALL(gas, target, V, 0,0,0,0) -> flag at mem[0]
    c += b'\x5f\x5f\x5f\x5f' + push(V) + push(target) + push(200000) + b'\xf1' + push(0) + b'\x52'
    c += push(0x20) + push(0) + (b'\xfd' if revert else b'\xf3')
    return bytes(c)


def f0_code():
    c = bytearray(); off = [0x100]
    def rec():  # store top of stack at next record word
        c.extend(push(off[0]) + b'\x52'); off[0] += 32
    def snapshot(t):
        for a in (F0, F1, t):
            c.extend(push(a) + b'\x31'); rec()                                    # BALANCE
        # STATICCALL FACE.balanceOf(t): selector 0x70a08231 at mem[0x1000]
        c.extend(push(0x70a08231 << 224) + push(0x1000) + b'\x52' + push(t) + push(0x1004) + b'\x52')
        c.extend(push(0x20) + push(0x2000) + push(0x24) + push(0x1000) + push(FACE) + b'\x5a\xfa'); rec()
        c.extend(push(0x2000) + b'\x51'); rec()
        c.extend(push(LOCK) + b'\x5c'); rec(); c.extend(push(NZDC) + b'\x5c'); rec()
        c.extend(push(1) + b'\x54'); rec()
    return c, off, snapshot, rec


def program(target, revert):
    c, off, snapshot, rec = f0_code()
    c += push(1) + push(LOCK) + b'\x5d' + push(1) + push(NZDC) + b'\x5d' + push(5) + push(1) + b'\x55'
    snapshot(target)
    c += b'\x5f\x5f\x5f\x5f' + push(F1) + push(2_000_000) + b'\xf4'; rec()             # DELEGATECALL F1, flag
    c += b'\x3d\x5f' + push(0x3000) + b'\x3e' + push(0x3000) + b'\x51'; rec()         # F1's record (its CALL flag)
    snapshot(target)
    c += push(off[0] - 0x100) + push(0x100) + b'\xf3'
    return bytes(c)


def rpc(payload):
    for attempt in range(4):
        try:
            r = urllib.request.Request(URL, json.dumps(payload).encode(), {'Content-Type': 'application/json', 'User-Agent': 'curl/8'})
            return json.load(urllib.request.urlopen(r, timeout=90))
        except Exception as e:
            err = str(e); time.sleep(3 + 4 * attempt)
    return {'error': err}


def h(a, n=20): return '0x%0*x' % (2 * n, a)


cases = []
for name, target, revert, bl in (('accepted_in_reverted_frame', T_OK, True, False), ('rejected_in_reverted_frame', T_BL, True, True),
                                 ('accepted_in_committed_frame', T_OK, False, False), ('rejected_in_committed_frame', T_BL, False, True)):
    ov = {h(F0): {'code': '0x' + program(target, revert).hex(), 'balance': hex(10 ** 18)},
          h(F1): {'code': '0x' + f1_code(target, revert).hex(), 'balance': hex(10 ** 18)},
          h(FROM): {'balance': hex(10 ** 20)}}
    if target == T_OK: ov[h(T_OK)] = {'code': '0x00'}
    if bl: ov[h(NCC)] = {'stateDiff': {h(kw(T_BL, 2), 32): h(1, 32)}}
    cases.append((name, target, revert, bl, ov))

res = {'url': URL, 'clientVersionBefore': rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []}),
       'blockBefore': rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'eth_blockNumber', 'params': []}), 'cases': []}
for name, target, revert, bl, ov in cases:
    call = {'from': h(FROM), 'to': h(F0), 'gas': hex(5_000_000), 'input': '0x'}
    a = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{k: v for k, v in call.items() if k != 'input'}, 'latest', ov]})
    s = rpc({'jsonrpc': '2.0', 'id': 2, 'method': 'eth_simulateV1', 'params': [
        {'blockStateCalls': [{'stateOverrides': ov, 'calls': [call]}], 'validation': False, 'traceTransfers': False}, 'latest']})
    rec = {'case': name, 'target': h(target), 'f1Reverts': revert, 'blocklisted': bl, 'eth_call': a, 'simulate': s}
    if 'result' in a:
        w = bytes.fromhex(a['result'][2:]); ws = [int.from_bytes(w[i:i + 32], 'big') for i in range(0, len(w), 32)]
        names = ['balF0', 'balF1', 'balT', 'faceOk', 'faceBalT', 'tLock', 'tCount', 'slot1']
        before = dict(zip(names, ws[0:8])); flag, inner = ws[8], ws[9]; after = dict(zip(names, ws[10:18]))
        rec['decoded'] = {'before': before, 'f1CallFlag': flag, 'innerValueCallFlag': inner, 'after': after}
        exp_inner = 0 if bl else 1
        moved = (not revert) and (not bl)
        exp_after = dict(before)
        if moved:
            exp_after['balF0'] = before['balF0'] - V; exp_after['balT'] = before['balT'] + V
        if not revert:
            exp_after['tLock'] = 9; exp_after['tCount'] = 3; exp_after['slot1'] = 6
        rec['expected'] = {'f1CallFlag': 0 if revert else 1, 'innerValueCallFlag': exp_inner, 'after_without_face': {k: v for k, v in exp_after.items() if k not in ('faceBalT', 'faceOk')}}
        ok = flag == (0 if revert else 1) and inner == exp_inner and all(after[k] == v for k, v in exp_after.items() if k not in ('faceBalT', 'faceOk'))
        # the face reads the native balance: it must move exactly when the native balance of T moves
        ok = ok and ((after['faceBalT'] - before['faceBalT']) == 0) == (after['balT'] == before['balT'])
        rec['matches'] = ok
    if 'result' in s:
        try:
            logs = s['result'][0]['calls'][0].get('logs', [])
            rec['simLogs'] = [{'address': l['address'], 'topics': l['topics'], 'data': l['data']} for l in logs]
            rec['simStatus'] = s['result'][0]['calls'][0].get('status')
            rec['simReturn'] = s['result'][0]['calls'][0].get('returnData')
        except Exception as e:
            rec['simParseError'] = str(e)
    res['cases'].append(rec)
    time.sleep(1)
res['clientVersionAfter'] = rpc({'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []})
json.dump(res, open(OUT, 'w'), indent=1)
for r in res['cases']:
    print(r['case'], 'matches', r.get('matches'), 'decoded', json.dumps(r.get('decoded'))[:400], 'logs', len(r.get('simLogs', [])) if 'simLogs' in r else r.get('simulate', {}).get('error'))
