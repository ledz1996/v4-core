# A sync made inside an unlock that closes with zero deltas stays in place after the unlock returns. eth_call with state overrides only.
import json, os
from lib import *
from tests import E, B, FROM, overrides, tl
from show import dump
res = {}
for n in NETS:
    cid = n['chainId']; u = n['rpc']; pm = n['poolManager']
    inner = script(0, [item(pm, cd('sync(address)', B)), tl(pm, NONZERO)])
    outer = script(0, [item(pm, unlock(inner)), tl(pm, IS_UNLOCKED), tl(pm, CURRENCY), tl(pm, NONZERO),
                       item(pm, unlock(script(0, [item(pm, cd('settle()'), 1)]))),          # a later payer in the same transaction that sends value without its own sync
                       item(pm, unlock(script(0, [item(pm, cd('sync(address)', 0)), item(pm, cd('settle()'), 1), item(pm, cd('take(address,address,uint256)', 0, FROM, 1))])))])
    r = rpc(u, 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + outer}, 'latest', overrides(pm, True)])
    lines = dump(r['result']) if 'result' in r else [json.dumps(r)[:200]]
    res[cid] = lines; print(cid, n['name'], ' | '.join(l.strip() for l in lines))
json.dump(res, open(os.path.join(HERE, 'raw', 'stale.json'), 'w'), indent=1)
