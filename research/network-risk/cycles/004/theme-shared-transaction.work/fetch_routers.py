# Fetch the verified source of every Universal Router and PositionManager listed in state/networks.json from Sourcify.
import json, concurrent.futures as cf
from lib import *
jobs=[]
for n in NETS:
    for k,v in n['contracts'].items():
        kk=k.replace(' ',' ')
        if kk.startswith('Universal Router') or kk=='PositionManager': jobs.append((n['chainId'],n['name'],kk,v))
def f(j):
    cid,name,k,a=j
    try: r=fetch_src(cid,a)
    except Exception as e: r='ERR '+repr(e)[:80]
    return (cid,name,k,a,r)
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(f,jobs))
json.dump(res,open('routers_fetched.json','w'),indent=1)
for r in res: print(r[0],r[1],r[2],r[3],(r[4][1],r[4][2]) if isinstance(r[4],(list,tuple)) else r[4])
