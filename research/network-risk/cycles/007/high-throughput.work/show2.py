import sys,pickle,collections
res=pickle.load(open(sys.argv[1],'rb'))
names={l.split()[0].lower():l.split()[1] for l in open(sys.argv[2]) if l.strip()}
only=sys.argv[3].split(',') if len(sys.argv)>3 else None
by=collections.OrderedDict()
for t,frame,kind,shape,p in res:
    by.setdefault(t,collections.OrderedDict()).setdefault((frame,kind),[]).append((shape,p))
for t,d in by.items():
    nm=names.get(t.lower(),'')
    if only and nm not in only: continue
    print('==',t,nm)
    for (frame,kind),lst in d.items():
        oks=[s for s,p in lst if p.get('ok')==1]
        revs=collections.Counter((p.get('ret','')[:8] if p.get('rds') else 'empty') if 'ok' in p else str(p)[:40] for s,p in lst if p.get('ok')!=1)
        okret=collections.Counter(('rds%d'%p['rds'])+(':'+p['ret'][:16] if p['rds'] else '') for s,p in lst if p.get('ok')==1)
        print(f'  {frame:6} {kind:21} ok {len(oks):2}/{len(lst):2} {",".join(oks)[:90]:90} okret={dict(okret)} rev={dict(revs)}'[:330])
