import glob,os,json
def ops(code):
    b=bytes.fromhex(code[2:]); i=0
    while i<len(b):
        op=b[i]; n=op-0x5f if 0x60<=op<=0x7f else 0
        yield i,op,b[i+1:i+1+n]; i+=1+n
res={}
for f in sorted(glob.glob('../raw/code/portal_*.hex'))+glob.glob('../raw/code/*inbox_0x*.hex'):
    c=open(f).read().strip(); L=list(ops(c))
    alias=[i for i,op,a in L if op==0x73 and a.hex()=='1111000000000000000000000000000000001111']
    origin=[i for i,op,a in L if op==0x32]
    ef=[i for i,op,a in L if op==0x62 and a.hex()=='ef0100']
    log4=[i for i,op,a in L if op==0xa4]
    # the TransactionDeposited topic
    td=[i for i,op,a in L if op==0x7f and a.hex()=='b3813568d9991fc951961fcb4c784893574240a28925604d09fc577c55bb7c32']
    res[os.path.basename(f)]={'aliasConstPUSH20':alias,'ORIGIN':origin,'PUSH3_ef0100':ef,'LOG4':len(log4),'TransactionDepositedTopic':td}
    print(os.path.basename(f)[:40],json.dumps(res[os.path.basename(f)]))
json.dump(res,open('../raw/bytescan.json','w'),indent=1)
