import json,time,concurrent.futures as cf
from width_probe import rpc,sel,W,NET
S1=sel('extsload(bytes32)'); S2=sel('extsload(bytes32,uint256)'); S3=sel('extsload(bytes32[])'); T1=sel('exttload(bytes32)'); T3=sel('exttload(bytes32[])')
LOCK=0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
def call(n,data):
    r=rpc(n['rpc'],'eth_call',[{'to':n['poolManager'],'data':'0x'+data},'latest'])
    return r.get('result') if isinstance(r,dict) else None
def run(n):
    slots=[0,1,2,3,6]
    single=[call(n,S1+W(s)) for s in range(0,7)]
    stor=[rpc(n['rpc'],'eth_getStorageAt',[n['poolManager'],hex(s),'latest']).get('result') for s in range(0,7)]
    rng=call(n,S2+W(0)+W(7))
    lst=call(n,S3+W(0x20)+W(7)+''.join(W(s) for s in range(7)))
    exp='0x'+W(0x20)+W(7)+''.join((x or '0x??')[2:] for x in single)
    zero=call(n,S2+W(5)+W(0))
    tl=call(n,T1+W(LOCK)); tl3=call(n,T3+W(0x20)+W(2)+W(LOCK)+W(LOCK-1))
    # wraparound at the top of the slot space: start 2^256-1, 2 slots -> slots (2^256-1, 0)
    wrap=call(n,S2+W((1<<256)-1)+W(2))
    return n['chainId'],{
      'single_eq_getStorageAt': all(a and b and int(a,16)==int(b,16) for a,b in zip(single,stor)),
      'range_eq': rng==exp, 'list_eq': lst==exp,
      'zero_len': zero=='0x'+W(0x20)+W(0),
      'exttload_lock_zero': tl=='0x'+W(0), 'exttload_list_zero': tl3=='0x'+W(0x20)+W(2)+W(0)+W(0),
      'wrap_second_is_slot0': (wrap or '')[-64:]==(single[0] or '0x')[2:] and len(wrap or '')==2+64*4,
      'owner': single[0][-40:] if single[0] else None}
with cf.ThreadPoolExecutor(8) as ex:
    res=dict(ex.map(run,NET))
json.dump(res,open('extsload_probe.out.json','w'),indent=1)
for k,v in res.items(): print(k,v)
