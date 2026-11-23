# An unlock that only takes a codeless currency cannot close; one that takes amount 0 closes. eth_call with state overrides only.
import json, os, sys, time
from lib import *
from tests import E, SINK, X, FROM, overrides
p = os.path.join(HERE, 'raw', 'codeless_close.json')
res = json.load(open(p)) if os.path.exists(p) else {}
for n in NETS:
    cid = n['chainId']
    if sys.argv[1:] and str(cid) not in sys.argv[1:]: continue
    outer = script(0, [item(n['poolManager'], unlock(script(0, [item(n['poolManager'], cd('take(address,address,uint256)', X, SINK, 5))]))),
                       item(n['poolManager'], unlock(script(0, [item(n['poolManager'], cd('take(address,address,uint256)', X, SINK, 0))])))])
    r = rpc(n['rpc'], 'eth_call', [{'from': FROM, 'to': E, 'data': '0x' + outer}, 'latest', overrides(n['poolManager'], False)])
    res[str(cid)] = [short(ok, d)[:60] for ok, d in records(r['result'])] if 'result' in r else [json.dumps(r)[:160]]
    print(cid, res[str(cid)])
json.dump(res, open(p, 'w'), indent=1)
