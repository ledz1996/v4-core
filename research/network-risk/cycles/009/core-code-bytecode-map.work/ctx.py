import json,sys
ins=json.load(open('instrs.json')); cov=set(json.load(open('coverage-full.json'))['cover'])
ops=sys.argv[1].split(','); w=int(sys.argv[2]) if len(sys.argv)>2 else 7
for k,e in enumerate(ins):
    if e['op'] in ops and e['src']!='data':
        print('=== pc %d %s  [%s] %s  yul=%s cov=%s'%(e['pc'],e['op'],e['src'],e['fn'],e['yul'],e['pc'] in cov))
        print('    text:', e['text'].replace('\n',' ')[:150])
        for j in range(max(0,k-w),min(len(ins),k+4)):
            x=ins[j]; print('   %s%6d %-10s %-12s %s'%('>' if j==k else ' ',x['pc'],x['op'],x['imm'] or '',x['src']))
