import json,urllib.request,sys
A='0x00000000000000000000000000000000000c0ffe'
def rpc(u,m,p):
    r=urllib.request.Request(u,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={'content-type':'application/json','user-agent':'probe'})
    try: return json.load(urllib.request.urlopen(r,timeout=30))
    except Exception as e: return {'err':str(e)}
progs={
 'invalid_fe':'fe',
 'undefined_0c':'0c',
 'bad_jump':'600356',
 'jump_into_push':'6004565b00',  # dest 4 is inside? 60 04 56 5b 00 -> dest 4 is 00 STOP not JUMPDEST
 'jump_push_data_5b':'6003566000605b',
 'stack_underflow':'01',
 'mstore_huge':'600063ffffffff52',
 'mstore_u64max':'600067ffffffffffffffff52',
 'mstore_2p64':'6000680100000000000000005200',
 'mload_wrapping':'7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe051',
 'keccak_huge':'63ffffffff600020',
 'calldatacopy_hugeoff_zero_len':'60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff60003760206000f3',
 'returndatacopy_oob':'6001600060003e',
 'mcopy_huge_len0':'60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5e60206000f3',
 'stack_overflow':'5b5f600056',
 'oog_loop':'5b600056',
 'tstore_static':None,
}
out={}
for u in sys.argv[1:]:
    o={}
    for k,c in progs.items():
        if c is None: continue
        o[k]=rpc(u,'eth_call',[{'to':A,'gas':'0x200000'},'latest',{A:{'code':'0x'+c}}])
        o[k]=o[k].get('result') or o[k].get('error') or o[k]
    out[u]=o
print(json.dumps(out,indent=1))
