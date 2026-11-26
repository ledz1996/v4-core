"""usage: deployblock.py rpc head out.json addr...  -- binary search on eth_getCode for the first block with code"""
import sys,json; sys.path.insert(0,'scripts'); from rpc import call
U=sys.argv[1]; H=int(sys.argv[2]); out={'client':call(U,'web3_clientVersion',[]).get('result')}
for A in sys.argv[4:]:
    lo,hi=0,H; errs=0
    while hi-lo>1:
        m=(lo+hi)//2; r=call(U,'eth_getCode',[A,hex(m)])
        if 'error' in r: errs+=1; lo=m; continue
        if len(r['result'])>2: hi=m
        else: lo=m
    out[A]={'firstBlockWithCode':hi,'errors':errs}; print(A,out[A])
out['clientAfter']=call(U,'web3_clientVersion',[]).get('result')
json.dump(out,open(sys.argv[3],'w'),indent=1)
