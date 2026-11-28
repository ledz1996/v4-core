"""L-1303: replay multi-step swaps with each pool's tick spacing read from its Initialize log.
Read-only. Usage: python3 -I replay_sp.py <out.json> <swaps.json> [<swaps.json> ...]
Each sample is replayed with tools/opdiff/replay.py's transcription of Pool.swap, trying only the spacing
from the log. The spacing found is also checked against replay.py's fixed list."""
import sys, json, time, signal
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import replay as R
from evm import rpc, keccak

FIXED = list(R.SPACINGS)
STATE = {137: 'https://polygon.gateway.tenderly.co', 56: 'https://bsc-rpc.publicnode.com', 43114: 'https://api.avax.network/ext/bc/C/rpc'}
LOGS = {137: ['https://polygon.gateway.tenderly.co', 'https://polygon-bor-rpc.publicnode.com'],
        56: ['https://bsc-rpc.publicnode.com', 'https://bsc-dataseed1.bnbchain.org'],
        43114: ['https://api.avax.network/ext/bc/C/rpc', 'https://avalanche-c-chain-rpc.publicnode.com']}
PM = {137: '0x67366782805870060151383f4bbff9dab53e5cd6', 56: '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df', 43114: '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'}
TOPIC = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()

def spacing(cid, pool, upto):
    for url in LOGS[cid]:
        try:
            logs = rpc(url, 'eth_getLogs', [{'address': PM[cid], 'topics': [TOPIC, pool], 'fromBlock': '0x0', 'toBlock': hex(upto)}], timeout=60)
        except Exception as e:  # noqa
            continue
        if logs:
            w = int(logs[0]['data'][2 + 64:2 + 128], 16)
            return w - (1 << 256) if w >> 255 else w, url
    return None, None

def _alarm(*a):
    raise TimeoutError('time limit 300 s')

def main():
    out = sys.argv[1]
    signal.signal(signal.SIGALRM, _alarm)
    res = []
    chains = {cid: R.Chain(STATE[cid], PM[cid]) for cid in STATE}
    for src in sys.argv[2:]:
        for r in json.load(open(src))['results']:
            cid = r['chainId']
            if cid not in STATE:
                continue
            for kind in ('multiSamples', 'otherSamples'):
                for smp in r.get(kind, []):
                    t = time.time()
                    sp, url = spacing(cid, smp['pool'], smp['block'])
                    rec = {'src': src.split('/cycles/')[-1], 'chainId': cid, 'kind': kind[:-7], 'tx': smp['tx'], 'pool': smp['pool'],
                           'spacingFromLog': sp, 'logSource': url, 'inFixedList': sp in FIXED if sp is not None else None}
                    R.SPACINGS = [sp] if sp is not None else FIXED
                    signal.alarm(300)
                    try:
                        rec.update(R.replay(chains[cid], smp))
                    except Exception as e:  # noqa
                        rec.update({'ok': False, 'why': str(e)[:120]})
                    signal.alarm(0)
                    rec['secs'] = round(time.time() - t, 1)
                    res.append(rec)
                    print(json.dumps(rec), flush=True)
                    json.dump({'results': res}, open(out, 'w'), indent=1)
    summ = {}
    for x in res:
        k = '%s %s %s' % (x['src'], x['chainId'], x['kind'])
        a = summ.setdefault(k, {'n': 0, 'ok': 0, 'notInFixedList': 0, 'why': {}})
        a['n'] += 1; a['ok'] += int(bool(x.get('ok')))
        a['notInFixedList'] += int(x.get('inFixedList') is False)
        if not x.get('ok'):
            w = x.get('why', '')[:50]; a['why'][w] = a['why'].get(w, 0) + 1
    for k, v in summ.items():
        print(k, v)
    json.dump({'results': res, 'summary': summ}, open(out, 'w'), indent=1)

if __name__ == '__main__':
    main()
