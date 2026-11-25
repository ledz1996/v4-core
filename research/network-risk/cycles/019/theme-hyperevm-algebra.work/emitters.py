"""Factory of every unvalidated Swap emitter of the cycle 15 window (read-only eth_call on the archive client)."""
import json, sys, concurrent.futures as cf
sys.path.insert(0,'.')
from rpcu import rpc
U='https://rpc.purroofgroup.com'
u=json.load(open('../../018/theme-hyperevm-v3-rest.work/out/unvalidated-emitters.json'))
sw=u['swaps']
print('clientVersion', rpc(U,'web3_clientVersion',[]))
def f(a):
    try: return a, '0x'+rpc(U,'eth_call',[{'to':a,'data':'0xc45a0155'},'latest'])[-40:]
    except Exception as e: return a, None
out={}
with cf.ThreadPoolExecutor(8) as ex:
    for a,fa in ex.map(f, list(sw)): out[a]={'factory':fa,'swaps':sw[a]}
print('clientVersion', rpc(U,'web3_clientVersion',[]))
json.dump(out, open('out/emitters.json','w'), indent=0)
import collections
c=collections.Counter(); n=collections.Counter()
for a,v in out.items(): c[v['factory']]+=v['swaps']; n[v['factory']]+=1
for k,v in c.most_common(10): print(k,v,n[k])
