"""Run every case through eth_call on a network's public endpoint, read-only, at the real PoolManager address.
Usage: python3 chainrun26.py <cases.json> <outdir> <chainId> [rpc url or -]
Overrides: this checkout's build at the real PoolManager address (immutable set to it) with balance PM_BAL, the driver at
D (balance D_BAL) and S, the hook double at every hook address of the batch, the token double and forwarders, and the
rejecting contract. Each batch is bracketed by web3_clientVersion and pinned to the block number read just before it.
Nothing is sent."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common26 import *  # noqa
from evm import rpc

NETS = {n['chainId']: n for n in json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']}


def main():
    cases = json.load(open(sys.argv[1]))['cases']
    outdir = sys.argv[2]; cid = int(sys.argv[3]); n = NETS[cid]
    url = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else n['rpc']
    pm = int(n['poolManager'], 16)
    gas = int(os.environ.get('GAS', '30000000')); bs = int(os.environ.get('BS', '8'))
    rec = {'chainId': cid, 'name': n['name'], 'rpc': url, 'pm': n['poolManager'], 'gas': gas, 'batches': [], 'results': {}}
    queue = [cases[j:j + bs] for j in range(0, len(cases), bs)]
    t0 = time.time()
    while queue:
        chunk = queue.pop(0); b = {'ids': [c['id'] for c in chunk]}
        try: b['clientBefore'] = rpc(url, 'web3_clientVersion', [])
        except Exception as e: b['clientBefore'] = 'error: ' + str(e)[:200]  # noqa
        err = None
        for k in range(3):
            try:
                blk = rpc(url, 'eth_blockNumber', []); b['block'] = int(blk, 16)
                r = rpc(url, 'eth_call', [{'from': '0x%040x' % EOA, 'to': '0x%040x' % D, 'data': '0x' + enc_run(chunk, pm).hex(), 'gas': hex(gas)},
                                          blk, overrides(pm, chunk)], timeout=120)
                res = dec_run(bytes.fromhex(r[2:])); err = None; break
            except Exception as e:  # noqa
                err = str(e)[:400]; time.sleep(2 * (k + 1))
        try: b['clientAfter'] = rpc(url, 'web3_clientVersion', [])
        except Exception as e: b['clientAfter'] = 'error: ' + str(e)[:200]  # noqa
        if err:
            b['error'] = err
            if len(chunk) > 1:
                h = len(chunk) // 2; queue[:0] = [chunk[:h], chunk[h:]]; b['split'] = True
            else:
                rec['results'][str(chunk[0]['id'])] = {'error': err}
            rec['batches'].append(b); continue
        for c, (uok, words, rv) in zip(chunk, res):
            rec['results'][str(c['id'])] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
        rec['batches'].append(b)
        print('batch', len(rec['results']), round(time.time() - t0), flush=True)
    rec['secs'] = round(time.time() - t0)
    json.dump(rec, open(os.path.join(outdir, f'chain-{cid}.json'), 'w'))
    print('done', cid, n['name'], len(rec['results']), sum(1 for v in rec['results'].values() if 'error' in v), rec['secs'], flush=True)


if __name__ == '__main__':
    main()
