import sys, collections
rel={}
for l in open(sys.argv[1]):
    a,b=l.split(); rel[int(a,16)]=int(b,16)
for s in sys.argv[2:]:
    start,n=s.split(':'); start=int(start,16); n=int(n)
    for c in range(0,n,256):
        base=start+8*c
        f=[rel.get(base+8*i) for i in range(256)]
        if None in f: print(hex(base),'short'); continue
        cnt=collections.Counter(f); top=cnt.most_common(1)[0]
        # distinct handlers among 0x01..0x1d
        print(hex(base),'distinct',len(cnt),'top',hex(top[0]),top[1],'arith distinct',len(set(f[1:0x1e])),'0x00',hex(f[0]),'0x01',hex(f[1]),'0x56',hex(f[0x56]),'0x5c',hex(f[0x5c]), 'fe', hex(f[0xfe]), 'top==0x0c', f[0x0c]==top[0])
