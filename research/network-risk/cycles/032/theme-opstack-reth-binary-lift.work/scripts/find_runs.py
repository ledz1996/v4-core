import sys
rel={}
for l in open(sys.argv[1]):
    a,b=l.split(); rel[int(a,16)]=int(b,16)
keys=sorted(rel)
for stride in (8,16,24,32):
    seen=set()
    for a in keys:
        if a in seen: continue
        n=0;x=a
        while x in rel: seen.add(x); n+=1; x+=stride
        if n>=200: print(stride, hex(a), n, 'distinct', len(set(rel[a+stride*i] for i in range(n))))
