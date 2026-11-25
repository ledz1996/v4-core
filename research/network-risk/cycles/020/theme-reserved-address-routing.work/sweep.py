# Task 3/4: per network, (a) a sweeper placed by state override CALLs each listed address with empty calldata
# and a fixed 200,000 gas stipend, recording success, returndatasize and gas used (GAS before minus GAS after,
# so it includes the CALL base, cold/warm access and the callee); (b) direct eth_call + eth_estimateGas from a
# plain address for the PoolManager and pmdiff addresses; (c) a code-override check at reserved addresses:
# the same stub (returns word 0x2a) is set by override at each address and called with balanceOf(PM).
# Read-only: eth_call / eth_estimateGas / web3_clientVersion only.
import json,sys,time
sys.path.insert(0,'.')
from rpc import rpc
NETS=json.load(open('../../../state/networks.json'))
NETS=NETS if isinstance(NETS,list) else NETS['networks']
def asm():
    c=bytearray()
    c+=bytes([0x5f])                       # PUSH0 i
    loop=len(c); c+=bytes([0x5b])          # JUMPDEST
    c+=bytes([0x80,0x36,0x11,0x15])        # DUP1 CALLDATASIZE GT ISZERO  (cds>i)? -> iszero
    c+=bytes([0x61,0,0]); endfix=len(c)-2  # PUSH2 end
    c+=bytes([0x57])                       # JUMPI
    c+=bytes([0x80,0x35])                  # DUP1 CALLDATALOAD -> addr
    c+=bytes([0x5a])                       # GAS g0
    c+=bytes([0x5f]*5)                     # outSize outOff inSize inOff value
    c+=bytes([0x86])                       # DUP7 addr
    c+=bytes([0x62,0x03,0x0d,0x40])        # PUSH3 200000
    c+=bytes([0xf1])                       # CALL -> succ
    c+=bytes([0x90,0x5a,0x90,0x03])        # SWAP1 GAS SWAP1 SUB -> used
    c+=bytes([0x3d,0x60,0x40,0x1b,0x17])   # RETURNDATASIZE PUSH1 64 SHL OR
    c+=bytes([0x90,0x60,0xf8,0x1b,0x17])   # SWAP1 PUSH1 248 SHL OR -> word
    c+=bytes([0x82,0x52,0x50])             # DUP3 MSTORE POP
    c+=bytes([0x60,0x20,0x01])             # PUSH1 32 ADD
    c+=bytes([0x61,loop>>8,loop&0xff,0x56])# PUSH2 loop JUMP
    end=len(c); c+=bytes([0x5b,0x36,0x5f,0xf3]) # JUMPDEST CALLDATASIZE PUSH0 RETURN
    c[endfix]=end>>8; c[endfix+1]=end&0xff
    return '0x'+c.hex()
SWEEPER='0x00000000000000000000000000000000005eeb01'
FROM='0x00000000000000000000000000000000000a11ce'
STUB='0x602a60005260206000f3'
PMDIFF=['0x00000000000000000000000000000000504d0001','0x00000000000000000000000000000000d21fe001','0x00000000000000000000000000000000d21fe006',
 '0x00000000000000000000000000000000c0ffee01','0x00000000000000000000000000000000c0ffee02','0x00000000000000000000000000000000c0ffee05',
 '0x00000000000000000000000000000000c0ffee0a','0x00000000000000000000000000000000c0ffee0b','0x00000000000000000000000000000000c0ffee0c',
 '0x00000000000000000000000000000000c0ffee0d','0x00000000000000000000000000000000c0ffee0e','0x00000000000000000000000000000000486b0000',
 '0x00000000000000000000000000000000486b2080','0x00000000000000000000000000000000486b3fff','0x00000000000000000000000000000000486c0000',
 '0x000000000000000000000000000000000000beef','0x00000000000000000000000000000000000a11ce','0x00000000000000000000000000000000000c0de5',
 '0x000000000004444c5dc75cb358380d2e3de08a90','0x00000000000000000000000000000000005eeb01']
def H(x): return '0x'+('%x'%x).rjust(40,'0')
RESERVED={
 56:['0xca52'+'00'*8+'%02x'%o+'%018x'%1 for o in (0,1,2,0xff)]+['0xca5f000000000000000000000000000000000000','0x7020000000000000000000000000000000000001','0x7020000000000000000000000000000000000002',H(0x70),H(0x1000),H(0x2000)],
 8453:['0xb2000000000000000000002feb517dfec7415344','0xb2000000000000000000000d8ce462e99ee7a47b','0xb200000000000000000001000000000000000001','0xb200000000000000000000000000000000000000','0xb200000000000000000000000000000000000001'],
 4217:['0x20c0000000000000000000000000000000000000','0x20c0000000000000000000000000000000000001','0x20c000000000000000000000030a4c7f7b8f3586','0x20c0000000000000000000006a37da5c996874be','0x20c00000000000000000000000000000000fffff','0xfeec000000000000000000000000000000000000','0x403c000000000000000000000000000000000000','0x20fc000000000000000000000000000000000000','0xdec0000000000000000000000000000000000000'],
 5042:['0x3600000000000000000000000000000000000000','0x3600000000000000000000000000000000000001','0x3600000000000000000000000000000000000004','0x1800000000000000000000000000000000000005','0x1800000000000000000000000000000000000009'],
 999:[H(x) for x in range(0x800,0x814)]+['0x2222222222222222222222222222222222222222','0x3333333333333333333333333333333333333333','0x2000000000000000000000000000000000000000','0x2000000000000000000000000000000000000077','0x5555555555555555555555555555555555555555'],
}
def pad(a): return a[2:].lower().rjust(64,'0')
def run(n):
    cid=n['chainId']; u=n['rpc']; pm=n['poolManager'].lower()
    rec={'chainId':cid,'rpc':u}
    rec['clientVersionBefore']=rpc(u,'web3_clientVersion',[]).get('result')
    addrs=[H(i) for i in range(1,0x200)]+[pm]+PMDIFF+RESERVED.get(cid,[])
    cd='0x'+''.join(pad(a) for a in addrs)
    j=rpc(u,'eth_call',[{'from':FROM,'to':SWEEPER,'data':cd,'gas':hex(150_000_000)},'latest',{SWEEPER:{'code':asm()}}],timeout=120)
    if 'result' not in j:
        j=rpc(u,'eth_call',[{'from':FROM,'to':SWEEPER,'data':cd,'gas':hex(30_000_000)},'latest',{SWEEPER:{'code':asm()}}],timeout=120)
    sweep={}
    if 'result' in j:
        r=bytes.fromhex(j['result'][2:])
        for k,a in enumerate(addrs):
            w=int.from_bytes(r[32*k:32*k+32],'big')
            sweep[a]={'ok':w>>248,'rds':(w>>64)&((1<<64)-1),'used':w&((1<<64)-1)}
    else: sweep={'error':j}
    rec['sweep']=sweep
    direct={}
    for a in [pm]+PMDIFF[:3]:
        p={'from':FROM,'to':a,'data':'0x'}
        c=rpc(u,'eth_call',[p,'latest']); e=rpc(u,'eth_estimateGas',[p,'latest'])
        time.sleep(0.3)
        direct[a]={'call':c.get('result',c.get('error',c)),'estimateGas':e.get('result',e.get('error',e))}
    rec['direct']=direct
    ov={}
    for a in RESERVED.get(cid,[])+[H(i) for i in (1,2,4,0x64,0x100,0x101,0x1ff)]:
        data='0x70a08231'+pad(pm)
        p={'from':FROM,'to':a,'data':data,'gas':hex(2_000_000)}
        c0=rpc(u,'eth_call',[p,'latest']); c1=rpc(u,'eth_call',[p,'latest',{a:{'code':STUB}}])
        g=lambda c: c.get('result',c.get('error',c))
        ov[a]={'noOverride':g(c0),'stubOverride':g(c1)}
        time.sleep(0.3)
    rec['override']=ov
    rec['clientVersionAfter']=rpc(u,'web3_clientVersion',[]).get('result')
    return rec
if __name__=='__main__':
    want=[int(x) for x in sys.argv[1:]] or [n['chainId'] for n in NETS]
    out={}
    for n in NETS:
        if n['chainId'] not in want: continue
        try: out[n['chainId']]=run(n)
        except Exception as e: out[n['chainId']]={'exception':str(e)}
        r=out[n['chainId']]; print(n['chainId'],r.get('clientVersionBefore'),'sweep ok' if 'error' not in r.get('sweep',{'error':1}) else r.get('sweep'),flush=True)
        json.dump(out,open('raw/sweep_%s.json'%('all' if not sys.argv[1:] else '_'.join(sys.argv[1:])),'w'),indent=1)
