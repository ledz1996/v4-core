# Which routers hold the transient slot constants of the synced currency or the synced reserves in their code
# (a contract that reads them through exttload must carry the constant).
import json, concurrent.futures as cf
from lib import *
CUR=bytes.fromhex('27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9'); RES=bytes.fromhex('1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95')
CNT=bytes.fromhex('7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b'); LOCK=bytes.fromhex('c090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23')
jobs={}
for n in NETS:
    for k,v in n['contracts'].items():
        kk=k.replace(' ',' ')
        if kk.startswith('Universal Router') or kk=='PositionManager': jobs[(n['chainId'],v.lower())]=kk
for x in json.load(open('senders_classified.json')):
    if 'err' in x: continue
    jobs.setdefault((x['chainId'],(x['impl'] or x['addr']).lower()),'sender %.0f%%'%0)
def f(k):
    cid,a=k
    try: c=bytes.fromhex(rpc(net(cid)['rpc'],'eth_getCode',[a,'latest'])[2:])
    except Exception as e: return (cid,a,'ERR')
    return (cid,a,dict(cur=CUR in c,res=RES in c,cnt=CNT in c,lock=LOCK in c))
with cf.ThreadPoolExecutor(12) as ex: res=list(ex.map(f,list(jobs)))
json.dump([[r[0],r[1],jobs[(r[0],r[1])],r[2]] for r in res],open('slot_reads.json','w'),indent=1)
tot=0
for cid,a,r in res:
    if r=='ERR': print(cid,a,'ERR'); continue
    tot+=1
    if r['cur'] or r['res']: print(cid,a,jobs[(cid,a)],r)
print('contracts scanned',tot,'canonical with cur/res:',sum(1 for cid,a,r in res if r!='ERR' and (r['cur'] or r['res']) and not jobs[(cid,a)].startswith('sender')))
