"""Task 2: run every case through eth_call on a network's public endpoint, read-only, at the real PoolManager address.

Usage: python3 chainrun.py <allcases.json> <outdir> <chainId> [rpc url] [steps per batch]
State overrides: the build of this checkout at the real PoolManager address (immutable set to that address), the
driver at D and S, the token double at IMPL, forwarders at the case currencies, and the override storage of kind 7
cases as stateDiff on the PoolManager. Every batch is bracketed by web3_clientVersion. The block is pinned per batch
(eth_blockNumber just before the call). Nothing is sent; eth_call only.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
from evm import rpc

NETS = {n['chainId']: n for n in json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']}


def call(url, data, ov, blk, gas):
    return rpc(url, 'eth_call', [{'from': '0x%040x' % EOA, 'to': '0x%040x' % D, 'data': '0x' + data.hex(), 'gas': hex(gas)}, blk, ov],
               timeout=120)


def ov_for(pm, chunk):
    ov = overrides(pm, chunk)
    sd = {}
    for c in chunk:
        for k, v in c.get('storage', {}).items(): sd['0x%064x' % int(k, 16)] = '0x%064x' % int(v, 16)
    if sd: ov['0x%040x' % pm]['stateDiff'] = sd
    return ov


def main():
    allc = json.load(open(sys.argv[1])); cases = allc['cases']
    outdir = sys.argv[2]; cid = int(sys.argv[3]); n = NETS[cid]
    url = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else n['rpc']
    budget = int(sys.argv[5]) if len(sys.argv) > 5 else 400000
    ref = json.load(open(os.path.join(outdir, 'ref-eth.json')))
    steps = {}  # approximate cost per case from the reference run (number of distinct sides is not a cost; use 1)
    pm = int(n['poolManager'], 16)
    gas = int(os.environ.get('GAS', '30000000'))
    rec = {'chainId': cid, 'name': n['name'], 'rpc': url, 'pm': n['poolManager'], 'gas': gas, 'batches': [], 'results': {}}
    # batches: group cases of similar kind; size from env
    bs = int(os.environ.get('BS', '12'))
    i = 0; t0 = time.time()
    queue = [cases[j:j + bs] for j in range(0, len(cases), bs)]
    while queue:
        chunk = queue.pop(0)
        b = {'ids': [c['id'] for c in chunk]}
        try:
            b['clientBefore'] = rpc(url, 'web3_clientVersion', [])
        except Exception as e:  # noqa
            b['clientBefore'] = 'error: ' + str(e)[:200]
        err = None
        for k in range(4):
            try:
                blk = rpc(url, 'eth_blockNumber', []); b['block'] = int(blk, 16)
                ret = bytes.fromhex(call(url, enc_run(chunk), ov_for(pm, chunk), blk, gas)[2:])
                res = dec_run(ret); err = None
                break
            except Exception as e:  # noqa
                err = str(e)[:400]; time.sleep(2 * (k + 1))
        try:
            b['clientAfter'] = rpc(url, 'web3_clientVersion', [])
        except Exception as e:  # noqa
            b['clientAfter'] = 'error: ' + str(e)[:200]
        if err:
            b['error'] = err
            if len(chunk) > 1:
                h = len(chunk) // 2; queue[:0] = [chunk[:h], chunk[h:]]; b['split'] = True
            else:
                rec['results'][chunk[0]['id']] = {'error': err}
            rec['batches'].append(b); continue
        for c, (uok, words, rv) in zip(chunk, res):
            rec['results'][c['id']] = {'ok': uok, 'w': [hex(x) for x in words] if words else None, 'revert': rv.hex()}
        rec['batches'].append(b)
        i += len(chunk)
        if len(rec['batches']) % 20 == 0:
            print(cid, i, len(cases), round(time.time() - t0), flush=True)
    od = allc.get('outside')
    if od:
        try:
            blk = rpc(url, 'eth_blockNumber', [])
            ret = bytes.fromhex(rpc(url, 'eth_call', [{'from': '0x%040x' % EOA, 'to': '0x%040x' % D,
                                                       'data': '0x' + enc_bytes_array(SEL_OUTSIDE, [bytes.fromhex(x['data']) for x in od]).hex(),
                                                       'gas': hex(gas)}, blk, overrides(pm, [])], timeout=120)[2:])
            rec['outside'] = {'block': int(blk, 16), 'res': dec_outside(ret)}
        except Exception as e:  # noqa
            rec['outside'] = {'error': str(e)[:400]}
    rec['secs'] = round(time.time() - t0)
    json.dump(rec, open(os.path.join(outdir, f'chain-{cid}.json'), 'w'))
    print('done', cid, n['name'], len(rec['results']), rec['secs'], flush=True)


if __name__ == '__main__':
    main()
