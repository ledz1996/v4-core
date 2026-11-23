import sys; sys.path.insert(0,'.')
from lib import *
STUB='0x3660409003806040600037600060008260006020356000355af16000523d600060203e3d6020016000f3'
PMA=PM[8453]
EOA='0x00000000000000000000000000000000000a11ce'
SINK='0x000000000000000000000000000000000000beef'
def pad(a): return a.lower().replace('0x','').rjust(64,'0')
def fwd(target,value,payload,chain=8453,pm=None,extra=None):
    pm=pm or PM[chain]
    data='0x'+pad(target)+hex(value)[2:].rjust(64,'0')+payload.replace('0x','')
    ov={pm:{'code':STUB,'balance':hex(10**18)}}
    if extra: ov.update(extra)
    r=call(chain,pm,data,frm=EOA,override=ov)
    if 'result' in r:
        res=r['result'][2:]
        return int(res[:64],16), res[64:]
    return None, r['error'].get('message','')[:200]
sels={'empty':'','transfer0':'a9059cbb'+pad(SINK)+pad('0'),'transfer1':'a9059cbb'+pad(SINK)+pad('1'),'balanceOf':'70a08231'+pad(PMA),'unlockCallback':'91dd7346'+pad('20')+pad('0'),
 'beforeInit':'dc98354e','afterInit':'6fe7e6eb','beforeAdd':'259982e5','afterAdd':'9f063efc','beforeRem':'21d0ee70','afterRem':'6c2bbe7e','beforeSwap':'575e24b4','afterSwap':'b47b2fb1','beforeDonate':'b6a8b0fa','afterDonate':'e1b4af69'}
if __name__=='__main__':
    T={'factory':'0xB20f000000000000000000000000000000000000','policyReg':'0x8453000000000000000000000000000000000002','activationReg':'0x8453000000000000000000000000000000000001','txContext':'0x813000000000000000000000000000000000aa02','nonceMgr?':'0x813000000000000000000000000000000000aa01','OUSD':'0xB2000000000000000000002fEb517dFeC7415344','B20b':'0xb2000000000000000000000d8ce462e99ee7a47b','uncreated':'0xb200000000000000000001000000000000000001','0x8130..aa03':'0x813000000000000000000000000000000000aa03','0x8130..aa00':'0x813000000000000000000000000000000000aa00'}
    out={}
    for n,t in T.items():
        row={}
        for s,p in sels.items():
            for v in ((0,1) if s=='empty' else (0,)):
                ok,ret=fwd(t,v,p)
                row[f'{s}/{v}']=(ok,ret[:140])
        out[n]=row
        nz={k:v for k,v in row.items() if v[0]!=0}
        print(n,t,'non-reverting:',nz)
        print('    sample reverts:',{k:v[1][:72] for k,v in list(row.items())[:5]})
    json.dump(out,open('raw/sweep_base_special.json','w'),indent=1)
