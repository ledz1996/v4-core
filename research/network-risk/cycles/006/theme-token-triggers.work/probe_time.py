# Which endpoints honour a block override of the time in eth_call (4th parameter)?
import json, sys
from base import *
out = {}
P = '0x00000000000000000000000000000000000a55e7'
for n in NETS:
    cid = n['chainId']; out[cid] = {}
    for u in urls2(cid) + [x for x in CFG_STATE(cid)] if False else urls2(cid):
        try:
            r0 = ecall_t(cid, u, P, '0x', {P: {'code': TS_STUB}}, timeout=20)
            now = int(r0[2:66], 16)
            r1 = ecall_t(cid, u, P, '0x', {P: {'code': TS_STUB}}, dt=400 * 86400, now=now, timeout=20)
            ok = isinstance(r1, str) and int(r1[2:66], 16) == now + 400 * 86400
            out[cid][u] = dict(now=now, ok=ok, r=(r1 if not ok else None))
        except Exception as e:
            out[cid][u] = dict(err=str(e)[:100])
    print(cid, n['name'], {u: (v.get('ok'), str(v.get('r') or v.get('err'))[:90]) for u, v in out[cid].items()}, flush=True)
json.dump(out, open(os.path.join(RAW6, 'time_override.json'), 'w'), indent=1)
