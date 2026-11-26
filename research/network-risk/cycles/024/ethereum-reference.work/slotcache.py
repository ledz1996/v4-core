"""Probe for a per-frame SLOAD cache (erigon v3.8 frameSlots): does a frame read a stale slot after a nested frame
wrote it, after a nested write was reverted, or after a delegatecall wrote it? Read-only eth_call with state
override; each call is bracketed by web3_clientVersion. Usage: python3 slotcache.py <out.json> <url> <rounds>"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
A = '0x00000000000000000000000000000000005107ca'
B = '0x00000000000000000000000000000000005107cb'
def push(v):
    b = v.to_bytes(max(1, (v.bit_length() + 7) // 8), 'big')
    return bytes([0x5f + len(b)]) + b if v else b'\x5f'
# A: calldatasize 0 -> outer; calldata byte 0x01 -> inner write 7 and stop; 0x02 -> write 9 and revert
inner = b''
# layout: if calldatasize == 0 jump outer
outer = []
def asm():
    c = bytearray()
    c += b'\x36\x15'                          # iszero(calldatasize)
    c += b'\x60\x00\x57'                       # PUSH1 placeholder, JUMPI; target patched below
    jpos = len(c) - 2
    # inner: mode = byte0 of calldata
    c += push(0) + b'\x35' + push(248) + b'\x1c'   # mode
    c += push(1) + b'\x14'                   # eq(mode, 1)
    c += b'\x60\x00\x57'; j1 = len(c) - 2      # jump w7
    c += push(9) + push(1) + b'\x55'          # sstore(1, 9)
    c += push(0) + push(0) + b'\xfd'          # revert
    w7 = len(c); c += b'\x5b' + push(7) + push(1) + b'\x55' + b'\x00'
    outer_at = len(c)
    c += b'\x5b'
    c += push(1) + b'\x54' + push(0x00) + b'\x52'     # m[0]=sload(1)
    c += push(1) + b'\x54' + b'\x50'                   # sload(1) again, pop
    c += push(2) + b'\x54' + b'\x50'                   # sload(2) (second cache entry), pop
    # call self with calldata 0x01
    c += push(1 << 248) + push(0x200) + b'\x52'
    c += push(0) + push(0) + push(1) + push(0x200) + push(0) + b'\x30' + b'\x5a' + b'\xf1' + b'\x50'
    c += push(1) + b'\x54' + push(0x20) + b'\x52'      # m[0x20]=sload(1) expect 7
    c += push(1) + b'\x54' + b'\x50'
    # call self with 0x02 (write 9 then revert)
    c += push(2 << 248) + push(0x200) + b'\x52'
    c += push(0) + push(0) + push(1) + push(0x200) + push(0) + b'\x30' + b'\x5a' + b'\xf1' + b'\x50'
    c += push(1) + b'\x54' + push(0x40) + b'\x52'      # expect 7
    c += push(1) + b'\x54' + b'\x50'
    # delegatecall B (writes 11 to slot 1)
    c += push(0) + push(0) + push(0) + push(0) + push(int(B, 16)) + b'\x5a' + b'\xf4' + b'\x50'
    c += push(1) + b'\x54' + push(0x60) + b'\x52'      # expect 11
    # own sstore then read
    c += push(13) + push(1) + b'\x55' + push(1) + b'\x54' + push(0x80) + b'\x52'  # expect 13
    c += push(0xa0) + push(0) + b'\xf3'
    c[jpos:jpos + 1] = bytes([outer_at]) if outer_at < 256 else None
    c[j1:j1 + 1] = bytes([w7])
    return bytes(c)
code = asm()
codeB = push(11) + push(1) + b'\x55' + b'\x00'
WANT = [5, 7, 7, 11, 13]
if __name__ == '__main__':
    out, url, rounds = sys.argv[1], sys.argv[2], int(sys.argv[3])
    rows = []
    ov = {A: {'code': '0x' + code.hex(), 'state': {'0x' + (1).to_bytes(32, 'big').hex(): '0x' + (5).to_bytes(32, 'big').hex()}}, B: {'code': '0x' + codeB.hex()}}
    for i in range(rounds):
        try:
            v0 = evm.rpc(url, 'web3_clientVersion', [], 20)
            r = evm.rpc(url, 'eth_call', [{'to': A, 'data': '0x', 'gas': hex(3_000_000)}, 'latest', ov], 30)
            v1 = evm.rpc(url, 'web3_clientVersion', [], 20)
            w = [int(r[2 + 64 * k: 2 + 64 * (k + 1)], 16) for k in range(5)]
            rows.append({'before': v0, 'after': v1, 'words': w, 'ok': w == WANT})
        except Exception as e:
            rows.append({'error': str(e)[:160]}); time.sleep(3)
        time.sleep(0.3)
    bad = [r for r in rows if 'words' in r and not r['ok']]
    by = {}
    for r in rows:
        if 'words' in r:
            for v in {r['before'], r['after']}: by[v] = by.get(v, 0) + 1
    pinned = {}
    for r in rows:
        if 'words' in r and r['before'] == r['after']: pinned[r['before']] = pinned.get(r['before'], 0) + 1
    json.dump({'url': url, 'want': WANT, 'calls': len(rows), 'answered': sum('words' in r for r in rows), 'wrong': len(bad), 'versionsSeen': by, 'pinnedBy': pinned, 'rows': rows}, open(out, 'w'), indent=1)
    print('answered', sum('words' in r for r in rows), 'wrong', len(bad), 'pinned', pinned, 'seen', by)
