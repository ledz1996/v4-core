# What does a hook hold? Native balance, ERC-20 balances and ERC-6909 claims at the PoolManager for the currencies of its pools. Read-only.
import sys, json, glob, collections
from lib import *
from config import CFG
from summ import load, census
def hold(cid, hook, maxcur=14):
    n = net(cid); pm = n['poolManager']; u = n['rpc']
    rows = [r for r in load(cid) if r[6] == hook]
    cur = collections.Counter()
    for r in rows: cur[r[2]] += 1; cur[r[3]] += 1
    curs = [c for c, _ in cur.most_common(maxcur)]
    out = {'native': None, 'cur': {}}
    for uu in [u] + CFG[cid]['state']:
        try:
            out['native'] = int(rpc(uu, 'eth_getBalance', [hook, 'latest']), 16)
            for c in curs:
                e = {}
                try: e['claims'] = int(call(uu, pm, 'balanceOf(address,uint256)', adr(hook) + adr(c)), 16)
                except Exception as ex: e['claims'] = 'err'
                if int(c, 16):
                    try: e['erc20'] = int(call(uu, c, 'balanceOf(address)', adr(hook)), 16)
                    except Exception as ex: e['erc20'] = 'err'
                    try: e['pmBal'] = int(call(uu, c, 'balanceOf(address)', adr(pm)), 16)
                    except Exception as ex: e['pmBal'] = 'err'
                e['n'] = cur[c]; out['cur'][c] = e
            break
        except Exception as ex: out['err'] = repr(ex)[:100]
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1])
    hooks = sys.argv[2:] or [json.load(open(f))['hook'] for f in glob.glob('raw/probe/%d_*.json' % cid)]
    for h in hooks:
        o = hold(cid, h.lower())
        nz = {c: e for c, e in o['cur'].items() if (isinstance(e.get('claims'), int) and e['claims'] > 0) or (isinstance(e.get('erc20'), int) and e['erc20'] > 0)}
        print(cid, h, 'pools', census(cid)[0].get(h.lower(), 0), 'native', o['native'], 'currencies checked', len(o['cur']), 'held:', json.dumps({c: {k: v for k, v in e.items() if k in ('claims', 'erc20', 'n')} for c, e in nz.items()}))
        json.dump(o, open('raw/probe/hold_%d_%s.json' % (cid, h.lower()), 'w'))
