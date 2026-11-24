# Sixteen shape sweep on Ethereum mainnet. Read only: eth_call with a state override that puts a forwarding stub at the
# PoolManager address, so the PoolManager address is msg.sender of an inner frame and tx.origin is an unrelated codeless account.
import sys, json; from lib import *; from asm import assemble; from targets import *
URL='https://ethereum-rpc.publicnode.com'
ORIGIN='0x'+keccak256(b'cycle-008-sweep-origin')[12:].hex()
RECIP='0x'+keccak256(b'cycle-008-sweep-recipient')[12:].hex()
# calldata: [0:20] target, [20:52] value, [52:] payload. Returns [ok][returndatasize][returndata]
FWD_CALL=assemble('''
0x34 CALLDATASIZE SUB
DUP1 0x34 0 CALLDATACOPY
0 0 DUP3 0 0x14 CALLDATALOAD 0 CALLDATALOAD 0x60 SHR GAS CALL
0 MSTORE POP
RETURNDATASIZE 0x20 MSTORE
RETURNDATASIZE 0 0x40 RETURNDATACOPY
RETURNDATASIZE 0x40 ADD 0 RETURN
''')
FWD_STATIC=assemble('''
0x34 CALLDATASIZE SUB
DUP1 0x34 0 CALLDATACOPY
0 0 DUP3 0 0 CALLDATALOAD 0x60 SHR GAS STATICCALL
0 MSTORE POP
RETURNDATASIZE 0x20 MSTORE
RETURNDATASIZE 0 0x40 RETURNDATACOPY
RETURNDATASIZE 0x40 ADD 0 RETURN
''')
KEY=[w('0x0000000000000000000000000000000000000000'), w('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'), w(3000), w(60)]
def key(h): return ''.join(KEY)+w(h)
PK='(address,address,uint24,int24,address)'; ML='(int24,int24,int256,bytes32)'; SP='(bool,int256,uint160)'
SQRT=79228162514264337593543950336
def dyn(headwords, data=''):  # append offset to bytes and the bytes
    off=(len(headwords)+1)*32
    return ''.join(headwords)+w(off)+w(len(data)//2)+pad32(data)
def shapes(t):
    ml=[w(-60),w(60),w(10**18),w(0)]; sp=[w(1),w(-10**18),w(4295128740)]
    S=[]
    S.append(('P1 empty value0','call',0,''))
    S.append(('P1 empty value1wei','call',1,''))
    S.append(('P1 empty value1eth','call',10**18,''))
    S.append(('P2 transfer(to,0)','call',0,cd('transfer(address,uint256)',RECIP,0)))
    S.append(('P2 transfer(to,1)','call',0,cd('transfer(address,uint256)',RECIP,1)))
    S.append(('P2 transfer(to,1e18)','call',0,cd('transfer(address,uint256)',RECIP,10**18)))
    S.append(('P3 balanceOf(PM) static','static',0,cd('balanceOf(address)',PM)))
    k=key(t)
    S.append(('P5 beforeInitialize','call',0,sel('beforeInitialize(address,%s,uint160)'%PK)+w(ORIGIN)+k+w(SQRT)))
    S.append(('P5 afterInitialize','call',0,sel('afterInitialize(address,%s,uint160,int24)'%PK)+w(ORIGIN)+k+w(SQRT)+w(0)))
    S.append(('P5 beforeAddLiquidity','call',0,sel('beforeAddLiquidity(address,%s,%s,bytes)'%(PK,ML))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+ml)))
    S.append(('P5 afterAddLiquidity','call',0,sel('afterAddLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,ML))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+ml+[w(0),w(0)])))
    S.append(('P5 beforeRemoveLiquidity','call',0,sel('beforeRemoveLiquidity(address,%s,%s,bytes)'%(PK,ML))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+ml)))
    S.append(('P5 afterRemoveLiquidity','call',0,sel('afterRemoveLiquidity(address,%s,%s,int256,int256,bytes)'%(PK,ML))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+ml+[w(0),w(0)])))
    S.append(('P5 beforeSwap','call',0,sel('beforeSwap(address,%s,%s,bytes)'%(PK,SP))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+sp)))
    S.append(('P5 afterSwap','call',0,sel('afterSwap(address,%s,%s,int256,bytes)'%(PK,SP))+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t)]+sp+[w(0)])))
    S.append(('P5 beforeDonate','call',0,sel('beforeDonate(address,%s,uint256,uint256,bytes)'%PK)+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t),w(1),w(1)])))
    S.append(('P5 afterDonate','call',0,sel('afterDonate(address,%s,uint256,uint256,bytes)'%PK)+dyn([w(ORIGIN),KEY[0],KEY[1],KEY[2],KEY[3],w(t),w(1),w(1)])))
    S.append(('P7 unlockCallback','call',0,sel('unlockCallback(bytes)')+w(0x20)+w(0)))
    return S
def valid_hook(a):
    x=int(a,16)&0x3fff
    def h(b): return bool(x>>b&1)
    # bits: 13 beforeInit,12 afterInit,11 beforeAdd,10 afterAdd,9 beforeRemove,8 afterRemove,7 beforeSwap,6 afterSwap,5 beforeDonate,4 afterDonate,3 beforeSwapRD,2 afterSwapRD,1 afterAddRD,0 afterRemoveRD
    if not h(7) and h(3): return False
    if not h(6) and h(2): return False
    if not h(10) and h(1): return False
    if not h(8) and h(0): return False
    return x>0
if __name__=='__main__':
    blk=sys.argv[1] if len(sys.argv)>1 else hex(int(rpc(URL,'eth_blockNumber',[])['result'],16)-2)
    out={'block':blk,'origin':ORIGIN,'recipient':RECIP,'rows':[]}
    for cat,label,addr in T:
        S=shapes(addr); batch=[]
        for i,(name,mode,val,data) in enumerate(S):
            code=FWD_CALL if mode=='call' else FWD_STATIC
            calld='0x'+addr[2:].lower()+w(val)+data
            batch.append({'jsonrpc':'2.0','id':i,'method':'eth_call','params':[{'from':ORIGIN,'to':PM,'data':calld,'gas':hex(12_000_000)},blk,{PM:{'code':code}}]})
        res=post(URL,batch)
        byid={x['id']:x for x in res} if isinstance(res,list) else {}
        for i,(name,mode,val,data) in enumerate(S):
            x=byid.get(i,{})
            if 'result' not in x: row={'cat':cat,'label':label,'addr':addr,'shape':name,'err':json.dumps(x.get('error'))[:200]}
            else:
                b=bytes.fromhex(x['result'][2:]); ok=int.from_bytes(b[:32],'big'); n=int.from_bytes(b[32:64],'big'); rd=b[64:64+n]
                verdict=''
                if name.startswith('P1'): verdict='native take passes' if ok else 'reverts'
                elif name.startswith('P2'): verdict='take passes' if ok and (n==0 or (n>=32 and int.from_bytes(rd[:32],'big')==1)) else 'reverts'
                elif name.startswith('P3'): verdict=('sync reads %d'%int.from_bytes(rd[:32],'big')) if ok and n>=32 else 'reverts'
                elif name.startswith('P5'): verdict='HOOK ACCEPTED' if ok and n>=32 and rd[:4].hex()==data[:8] else 'reverts'
                else: verdict='ok' if ok else 'reverts'
                row={'cat':cat,'label':label,'addr':addr,'shape':name,'ok':ok,'rds':n,'rd':rd[:96].hex(),'verdict':verdict}
            out['rows'].append(row)
        print(label, 'validHook=%s'%valid_hook(addr), '|', '; '.join('%s:%s'%(r['shape'].split(' ',1)[1][:22], ('ERR' if 'err' in r else ('%d/%d'%(r['ok'],r['rds'])))) for r in out['rows'][-len(S):]), flush=True)
    json.dump(out,open('raw_sweep.json','w'),indent=0)
