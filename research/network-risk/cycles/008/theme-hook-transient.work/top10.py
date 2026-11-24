# Top hooks per network by number of initialized pools, from the cycle 5 Initialize census.
from common import *
os.chdir(C5)
from summ import census, flags
out = {}
for n in NETS:
    cid = n['chainId']
    try: cnt, dyn, rows, total, cov = census(cid)
    except Exception as e: print(cid, 'ERR', e); continue
    z = '0x' + '0' * 40
    top = [(h, c) for h, c in cnt.most_common(40) if h != z][:int(sys.argv[1]) if len(sys.argv) > 1 else 10]
    out[cid] = dict(total=total, hooks=len(cnt) - (z in cnt), top=top)
    print(cid, n['name'], 'pools', total, 'hooks', out[cid]['hooks'], flush=True)
    for h, c in top: print('   ', h, c, ','.join(flags(h)))
json.dump(out, open(os.path.join(RAW, 'top10.json'), 'w'))
