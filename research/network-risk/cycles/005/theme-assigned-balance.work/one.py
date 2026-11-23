# One read-only trial of the assign sequence for a named token and call. Prints the eight result words.
import sys, json
from common import *
from asm import MULTI, FWD
from abi import split_types, encode
A = '0x00000000000000000000000000000000000a11ce'; SINK = '0x00000000000000000000000000000000005111c0'
def item(p):
    b = bytes.fromhex(p); return u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
def trial(cid, tok, calls, amt=None, frac=3, block='latest', target=None):
    """calls: list of (signature, values). Each is one separate trial; A calls target (default the token)."""
    pm = net(cid)['poolManager']
    if amt is None:
        r = ecall(cid, tok, sel('balanceOf(address)') + adr(pm), block=block)
        amt = int(r, 16) // frac
    items = [adr(tok) + sel('balanceOf(address)')[2:] + adr(pm)]
    for c in calls:
        sig, vals = c[0], c[1]; tg = c[2] if len(c) > 2 else (target or tok)
        vals = [pm if v == 'PM' else (A if v == 'A' else (amt if v == 'AMT' else v)) for v in vals]
        items.append(adr(tg) + sel(sig)[2:] + encode(split_types(sig), vals))
    data = '0x' + adr(tok) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(p) for p in items)
    r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=60_000_000, block=block)
    if not isinstance(r, str): return amt, r
    ws = [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(len(items))]
    return amt, ws
def show(cid, tok, calls, **kw):
    amt, ws = trial(cid, tok, calls, **kw)
    bn = rpc(urls2(cid)[0], 'eth_blockNumber', [])
    print('chain', cid, 'token', tok, 'block~', int(bn, 16), 'amt', amt)
    if not isinstance(ws, list): print('  ERR', ws); return
    names = ['BASE'] + [c[0] for c in calls]
    for nm, w in zip(names, ws):
        print('  %-60s b0=%d toA=%d call=%d b1=%d balA=%d full=%d part=%d final=%d' % ((nm[:60],) + tuple(w)))
    return amt, ws

from asm import FWDN
def seq(cid, tok, steps, amt=None, frac=3, block='latest'):
    """One trial in which A runs several calls in order. steps: list of (target or None, signature, values)."""
    pm = net(cid)['poolManager']
    if amt is None:
        amt = int(ecall(cid, tok, sel('balanceOf(address)') + adr(pm), block=block), 16) // frac
    def enc(steps):
        out = ''
        for tg, sig, vals in steps:
            vals = [pm if v == 'PM' else (A if v == 'A' else (amt if v == 'AMT' else v)) for v in vals]
            cd = sel(sig)[2:] + encode(split_types(sig), vals)
            b = bytes.fromhex(cd)
            out += adr(tg or tok) + u256(len(b)) + b.ljust((len(b) + 31) // 32 * 32, b'\0').hex()
        return out
    items = [enc([(None, 'balanceOf(address)', ['PM'])]), enc(steps)]
    data = '0x' + adr(tok) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(p) for p in items)
    r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWDN}}, gas=60_000_000, block=block)
    if not isinstance(r, str): print('ERR', r); return amt, None
    ws = [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(2)]
    print('chain', cid, 'token', tok, 'amt', amt)
    for nm, w in zip(['BASE', ' + '.join(s[1].split('(')[0] for s in steps)], ws):
        print('  %-50s b0=%d toA=%d call=%d b1=%d balA=%d full=%d part=%d final=%d' % ((nm[:50],) + tuple(w)))
    return amt, ws
