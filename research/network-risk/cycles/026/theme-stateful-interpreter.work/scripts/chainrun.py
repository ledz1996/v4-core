"""Run every sequence through one eth_call per sequence on a network's public endpoint. Read-only: eth_call with state
overrides only (the build of this checkout at the real PoolManager address, the driver, the hook double, token doubles).
Each call is bracketed by web3_clientVersion and pinned to the block number read just before it. The gas of the call is
tried at 50M first, then at 30M and 25M if the endpoint refuses the first (some cap eth_call gas); a sequence that does
not fit is split into halves that run as separate eth_calls, and the split is recorded.
Usage: python3 -I chainrun.py <outdir> <chainId> [rpc url or -] [names...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seqlib as S
from evm import rpc

NETS = {n['chainId']: n for n in json.load(open(os.path.join(S.NR, 'state', 'networks.json')))['networks']}


def cv(url):
    try:
        return rpc(url, 'web3_clientVersion', [], timeout=30)
    except Exception as e:  # noqa
        return 'error: ' + str(e)[:200]


def one(url, pm, steps, gas):
    b = {'clientBefore': cv(url), 'gas': gas, 'nsteps': len(steps)}
    try:
        blk = rpc(url, 'eth_blockNumber', [], timeout=30); b['block'] = int(blk, 16)
        r = rpc(url, 'eth_call', [{'from': '0x%040x' % S.EOA, 'to': '0x%040x' % S.D, 'data': '0x' + S.enc_run(steps).hex(),
                                   'gas': hex(gas)}, blk, S.overrides(pm)], timeout=180)
        b['raw'] = r
        b['steps'] = S.dec_run(bytes.fromhex(r[2:]))
    except Exception as e:  # noqa
        b['error'] = str(e)[:500]
    b['clientAfter'] = cv(url)
    return b


ALT = {1: ['https://eth.api.pocket.network', 'https://eth.drpc.org', 'https://eth-mainnet.public.blastapi.io'],
       8453: ['https://base-rpc.publicnode.com', 'https://base.drpc.org'], 42161: ['https://arbitrum-one-rpc.publicnode.com'],
       137: ['https://rpc-mainnet.matic.quiknode.pro', 'https://polygon.drpc.org'], 56: ['https://bsc-rpc.publicnode.com'],
       43114: ['https://avalanche-c-chain-rpc.publicnode.com'], 143: ['https://rpc-mainnet.monadinfra.com'],
       999: ['https://rpc.purroofgroup.com'], 42220: ['https://celo.api.onfinality.io/public']}


def refused(b):
    e = b.get('error', '')
    return 'HTTP Error 403' in e or 'HTTP Error 429' in e or 'Too Many' in e


def main():
    od = sys.argv[1]; cid = int(sys.argv[2]); n = NETS[cid]
    url = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != '-' else n['rpc']
    if url == 'auto':
        cands = [n['rpc']] + ALT.get(cid, [])
        for u in cands:
            if not cv(u).startswith('error'):
                url = u; break
        else:
            url = n['rpc']
    names = sys.argv[4:] or ['a64', 'b', 'c', 'd300', 'e', 'a512']
    pm = int(n['poolManager'], 16)
    salt = json.load(open(os.path.join(S.WORK, 'build', 'salt.json')))['salt']
    seqs = S.sequences(salt)
    tag = url.split('//')[1].split('/')[0]
    if os.environ.get('ERIGON_TAG'):
        tag += '-rep' + os.environ['ERIGON_TAG']
    path = os.path.join(od, f'chain-{cid}-{tag}.json')
    rec = json.load(open(path)) if os.path.exists(path) else {'chainId': cid, 'name': n['name'], 'rpc': url, 'pm': n['poolManager'], 'seqs': {}}
    for nm in names:
        t0 = time.time(); parts = [seqs[nm]]; done = []
        while parts:
            st = parts.pop(0); got = None
            for gas in (50_000_000, 30_000_000, 25_000_000):
                b = one(url, pm, st, gas)
                time.sleep(1.5)
                if 'error' not in b:
                    got = b; break
                last = b
                if refused(b):
                    break
            if got is None and refused(last):
                done.append(dict(last, refusedByEndpoint=True)); rec.setdefault('refusals', []).append({'seq': nm, 'error': last['error']})
                continue
            if got is None:
                if len(st) > 4 and nm.startswith('a'):
                    h = len(st) // 2
                    # keep the two setup steps at the head of each half so each half starts from initialised pools
                    parts[:0] = [st[:h], st[:2] + st[h:]]
                    done.append({'split': True, 'error': last['error'], 'clientBefore': last['clientBefore'], 'clientAfter': last['clientAfter']})
                    continue
                done.append(last)
            else:
                done.append(got)
        rec['seqs'][nm] = {'calls': done, 'secs': round(time.time() - t0)}
        print(cid, nm, [('err ' + c['error'][:80]) if 'error' in c else (c['gas'], c['nsteps'], c['clientBefore']) for c in done], flush=True)
        json.dump(rec, open(path, 'w'))


if __name__ == '__main__':
    main()
