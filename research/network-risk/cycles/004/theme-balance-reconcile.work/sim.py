# Read-only trigger test through the canonical Multicall3: balanceOf(PM), one public call, balanceOf(PM), in one eth_call.
from lib import *
from reconcile import enc_aggregate3, dec_aggregate3
def trigger_test(url, pm, token, target, data, block='latest', extra=()):
    bal = '0x70a08231' + adr(pm)
    calls = [(token, bal), (target, data), (token, bal)] + list(extra)
    r = rpc(url, 'eth_call', [{'to': MC3, 'data': enc_aggregate3(calls)}, block if isinstance(block, str) else hex(block)])
    d = dec_aggregate3(r)
    b0 = int.from_bytes(d[0][1][:32], 'big') if d[0][0] and d[0][1] else None
    b1 = int.from_bytes(d[2][1][:32], 'big') if d[2][0] and d[2][1] else None
    return dict(before=b0, triggerOk=d[1][0], triggerRet=d[1][1].hex()[:136], after=b1, delta=(b1 - b0) if b0 is not None and b1 is not None else None, extra=[(x[0], x[1].hex()[:136]) for x in d[3:]])
