import itertools, subprocess, sys, os, filecmp
O='/home/user/v4-core/research/network-risk/cycles/033/high-throughput.work/dl/monadmain'
D='dl/monadmain'
res={'same':0,'diff':[],'miss':[]}
for b in sorted(os.listdir(O)):
    if os.path.exists(f'{D}/{b}') and os.path.getsize(f'{D}/{b}')>20 and not open(f'{D}/{b}','rb').read(14).startswith(b'404: Not Found'): continue
    parts=b.split('_'); n=len(parts)-1; found=None
    # first two separators are category/vm
    for mask in itertools.product([0,1],repeat=n-2):
        s=parts[0]+'/'+parts[1]+'/'+parts[2]
        for i,m in enumerate(mask): s+=('/' if m else '_')+parts[i+3]
        r=subprocess.run(['curl','-s','-m','30','-o',f'{D}/{b}','-w','%{http_code}','https://raw.githubusercontent.com/category-labs/monad/main/'+s],capture_output=True,text=True)
        if r.stdout=='200': found=s;break
    if not found: res['miss'].append(b)
    elif filecmp.cmp(f'{O}/{b}',f'{D}/{b}',shallow=False): res['same']+=1
    else: res['diff'].append(found)
print(res)
