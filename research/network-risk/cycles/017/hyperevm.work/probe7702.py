import json,urllib.request,sys,time
PM='0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'; D='0x00000000000000000000000000000000d7702d70'
def rpc(u,m,p):
    for i in range(4):
        r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'probe'})
        try:
            j=json.load(urllib.request.urlopen(r,timeout=30))
            return j.get('result') if 'result' in j else {'error':j['error'].get('message')}
        except Exception as e: err=str(e); time.sleep(2)
    return {'err':err}
w=lambda x: hex(x)[2:].rjust(64,'0')
shapes={
 'transfer':'0xa9059cbb'+w(0xdead)+w(10**18),
 'balanceOf':'0x70a08231'+w(int(PM,16)),
 'empty_value':'',
 'beforeSwap':'0x575e24b4'+'00'*32*12,
}
out={}
for u in sys.argv[1:]:
    o={}
    for k in list(range(0x800,0x815)):
        tgt='0x'+hex(k)[2:].rjust(40,'0')
        code='0xef0100'+tgt[2:]
        for sn,data in shapes.items():
            call={'from':PM,'to':D,'gas':'0x200000','data':'0x'+data[2:] if data else '0x'}
            if sn=='empty_value': call['value']='0x1'
            ov={D:{'code':code}, PM:{'balance':'0xde0b6b3a7640000'}}
            o[f'{hex(k)}:{sn}']=rpc(u,'eth_call',[call,'latest',ov])
    # control: direct call to the precompile with the same shapes
    for k in (0x800,0x801,0x807,0x80e):
        tgt='0x'+hex(k)[2:].rjust(40,'0')
        o[f'direct {hex(k)}:balanceOf']=rpc(u,'eth_call',[{'from':PM,'to':tgt,'gas':'0x200000','data':shapes['balanceOf']},'latest'])
    out[u]=o
json.dump(out,open(sys.argv[0].replace('probe7702.py','out/probe7702.json'),'w'),indent=1)
for u in out:
    vals={}
    for k,v in out[u].items(): vals.setdefault(json.dumps(v)[:90],[]).append(k)
    print(u); [print('  ',len(ks),r,ks[:4]) for r,ks in vals.items()]
