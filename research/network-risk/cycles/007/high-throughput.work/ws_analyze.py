import json,collections,sys
M=[]
for l in open(sys.argv[1]):
    try: j=json.loads(l)
    except: continue
    if j.get('k')=='m': M.append(j)
    elif 'eof' in j: print('EOF',j)
h=lambda x:int(x,16) if isinstance(x,str) else x
print('mini-blocks',len(M),'capture seconds %.1f'%(M[-1]['t']-M[0]['t']),'txs',sum(len(m['txs']) for m in M))
# continuity of mini block numbers
nums=[h(m['mb']) for m in M]; gaps=sum(1 for a,b in zip(nums,nums[1:]) if b!=a+1); print('gaps in mini-block numbers',gaps)
# per EVM block
B=collections.OrderedDict()
for m in M: B.setdefault(h(m['bn']),[]).append(m)
full=list(B.items())[1:-1]
cnt=[len(v) for k,v in full]
print('EVM blocks fully captured',len(full),'mini-blocks per EVM block min/median/max',min(cnt),sorted(cnt)[len(cnt)//2],max(cnt))
dts=[(h(v[-1]['mt'])-h(v[0]['mt']))/1e6 for k,v in full]; print('span of mini-block timestamps inside an EVM block s: min %.3f max %.3f'%(min(dts),max(dts)))
ts=[h(v[0]['mt'])/1e6 for k,v in full]; d=[b-a for a,b in zip(ts,ts[1:])]; print('first mini-block to first mini-block of the next EVM block: min %.3f max %.3f'%(min(d),max(d)))
iv=[(h(b['mt'])-h(a['mt']))/1e3 for a,b in zip(M,M[1:])]; iv.sort(); print('mini-block interval ms: median %.2f p1 %.2f p99 %.2f max %.2f'%(iv[len(iv)//2],iv[len(iv)//100],iv[-len(iv)//100],iv[-1]))
# ordering inside mini-blocks: user txs only (type 0 and 2), tip = effective priority = gasPrice or maxPriorityFee
def tip(x):
    if x['ty']=='0x2': return h(x['tip'])
    return h(x['gp'])-1_000_000 if x['gp'] else 0
multi=0;sorted_desc=0;pairs=0;inv=0;same=0
SYS='0xa887dcb9d5f39ef79272801d05abdf707cfbbd1d'
for m in M:
    u=[x for x in m['txs'] if x['ty'] in('0x0','0x2') and x['f'].lower()!=SYS]
    if len(u)<2: continue
    multi+=1
    tl=[tip(x) for x in u]
    if all(a>=b for a,b in zip(tl,tl[1:])): sorted_desc+=1
    for a,b in zip(u,u[1:]):
        if a['f']==b['f']: continue
        pairs+=1
        if tip(b)>tip(a): inv+=1
        elif tip(b)==tip(a): same+=1
print('mini-blocks with two or more user txs',multi,'of which tips non-increasing',sorted_desc,'| neighbouring pairs from different senders',pairs,'later pays more',inv,'equal',same)
# across mini-blocks inside one EVM block: later mini-block tx pays more than an earlier one
cross=0;crossinv=0
for k,v in full:
    seq=[(h(m['mb']),tip(x),x['f']) for m in v for x in m['txs'] if x['ty'] in('0x0','0x2') and x['f'].lower()!=SYS]
    for (ma,ta,fa),(mb,tb,fb) in zip(seq,seq[1:]):
        if ma!=mb and fa!=fb:
            cross+=1; crossinv+= tb>ta
print('neighbouring pairs in different mini-blocks of one EVM block',cross,'later pays more',crossinv)
# position of deposits
dep=[(h(m['bn']),h(m['i']),i) for m in M for i,x in enumerate(m['txs']) if x['ty']=='0x7e']
print('deposit txs',len(dep),'mini-block index values',collections.Counter(d[1] for d in dep).most_common(4),'position in mini-block',collections.Counter(d[2] for d in dep).most_common(4))
# largest tx gas
g=sorted(((h(r['gu']),m['bn']) for m in M for r in m['rc']),reverse=True)[:5]; print('largest gasUsed in capture',g)
tips=sorted(tip(x) for m in M for x in m['txs'] if x['ty'] in('0x0','0x2') and x['f'].lower()!=SYS); print('tip quantiles wei: p10 %d p50 %d p90 %d max %d'%(tips[len(tips)//10],tips[len(tips)//2],tips[9*len(tips)//10],tips[-1]),'distinct',len(set(tips)))
