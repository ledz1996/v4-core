# Why does a full balance transfer from the PoolManager fail? eth_call with from = PoolManager, several amounts and two recipients.
# usage: python3 why2.py <chainId> <token> [token ...]
import sys, json
from lib import *
from rule import state_urls
SINK = '0x00000000000000000000000000000000005111c0'; EOA = '0x1111111111111111111111111111111111111111'
def dec(r):
    if isinstance(r, dict):
        e = r.get('error') or {}; m = str(e.get('message', ''))[:90]; d = e.get('data')
        if isinstance(d, str) and d.startswith('0x08c379a0') and len(d) > 138:
            try: m += ' | ' + bytes.fromhex(d[138:138 + 2 * int(d[74:138], 16)]).decode('utf8', 'replace')
            except Exception: pass
        elif isinstance(d, str): m += ' | ' + d[:74]
        return 'REVERT ' + m
    return 'ok ' + (r[:66] if r != '0x' else 'empty')
def probe(cid, tok, url=None):
    pm = net(cid)['poolManager'].lower(); u = url or state_urls(cid)[0]; out = {}
    def c(data, frm=pm, to=tok):
        j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'from': frm, 'to': to, 'data': data, 'gas': hex(3000000)}, 'latest']}, timeout=40)
        return j['result'] if 'result' in j else {'error': j.get('error')}
    b = c(sel('balanceOf(address)') + adr(pm)); b = int(b, 16) if isinstance(b, str) and len(b) >= 66 else 0
    out['balance'] = str(b)
    for nm in ('symbol()', 'name()'):
        r = c(sel(nm))
        try: out[nm[:-2]] = bytes.fromhex(r[130:130 + 2 * int(r[66:130], 16)]).decode('utf8', 'replace') if isinstance(r, str) and len(r) > 130 else None
        except Exception: out[nm[:-2]] = None
    for label, amt in (('full', b), ('half', b // 2), ('third', b // 3), ('1pct', b // 100), ('0.01pct', b // 10000), ('one', 1), ('zero', 0)):
        out[label] = dec(c(sel('transfer(address,uint256)') + adr(SINK) + u256(amt)))
    out['full_to_eoa'] = dec(c(sel('transfer(address,uint256)') + adr(EOA) + u256(b)))
    out['other_holder_one'] = dec(c(sel('transfer(address,uint256)') + adr(SINK) + u256(1), frm=EOA))
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1])
    for t in sys.argv[2:]: print(t, json.dumps(probe(cid, t), indent=0, ensure_ascii=False))
