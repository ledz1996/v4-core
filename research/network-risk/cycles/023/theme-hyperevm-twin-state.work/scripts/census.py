# Gas price 0 census. Blocks: every block with a PoolManager log (whole history) plus a seeded random sample over
# the whole chain. For each block, the replica's full block (system txs included) and the official block (regular
# txs only) are read; gas price 0 txs are grouped by sender (replica 'from', which nanoreth decodes from s) and target.
import json, sys, random, collections, time
from rpc import rpc, batch
R = sys.argv[1]; O = sys.argv[2]; out = sys.argv[3]; nrand = int(sys.argv[4]); seed = int(sys.argv[5]); latest = int(sys.argv[6])
logs = json.load(open('../raw/pm_logs_all_hyperlend.json'))['logs']
pmblocks = sorted({int(l['blockNumber'], 16) for l in logs})
rnd = random.Random(seed); randblocks = sorted(rnd.sample(range(1, latest), nrand))
res = {'replica': R, 'official': O, 'seed': seed, 'nrand': nrand, 'latest': latest,
       'clientVersionStart': {R: rpc(R, 'web3_clientVersion', []), O: rpc(O, 'web3_clientVersion', [])},
       'blocks': {}, 'errors': []}
def scan(blocks, tag, with_official):
    for i in range(0, len(blocks), 10):
        ch = blocks[i:i + 10]
        for k in range(6):
            try:
                rb = batch(R, [('eth_getBlockByNumber', [hex(b), True]) for b in ch], timeout=120); break
            except Exception as e:
                res['errors'].append([tag, ch[0], 'replica', str(e)[:150]]); time.sleep(5 * (k + 1)); rb = None
        ob = [None] * len(ch)
        if with_official:
            for k in range(6):
                try:
                    ob = batch(O, [('eth_getBlockByNumber', [hex(b), True]) for b in ch], timeout=120); break
                except Exception as e:
                    res['errors'].append([tag, ch[0], 'official', str(e)[:150]]); time.sleep(8 * (k + 1)); ob = [None] * len(ch)
            time.sleep(0.7)
        for j, b in enumerate(ch):
            r = rb[j] if rb else None; o = ob[j]
            ent = {'tag': tag}
            if isinstance(r, dict) and 'transactions' in r:
                txs = r['transactions']
                ent['n'] = len(txs)
                ent['zero'] = [[t['transactionIndex'], t['from'], t.get('to'), t['input'][:10], t['type'], t.get('value'), t['hash']]
                               for t in txs if t.get('gasPrice') is not None and int(t['gasPrice'], 16) == 0]
                ent['zeroFeeCap1559'] = [[t['transactionIndex'], t['from'], t.get('to'), t['type'], t['hash']] for t in txs
                                          if t.get('maxFeePerGas') is not None and int(t['maxFeePerGas'], 16) == 0]
                idx = [int(z[0], 16) for z in ent['zero']]
                ent['zeroNotLeading'] = idx != list(range(len(idx)))
                ent['baseFee'] = r.get('baseFeePerGas')
            else:
                ent['replicaErr'] = str(r)[:150]
            if isinstance(o, dict) and 'transactions' in o:
                ent['officialN'] = len(o['transactions'])
                ent['officialZero'] = [[t['hash'], t['from'], t.get('to'), t.get('gasPrice'), t.get('maxFeePerGas')] for t in o['transactions']
                                       if int(t.get('gasPrice') or '0x1', 16) == 0 or int(t.get('maxFeePerGas') or '0x1', 16) == 0]
            elif with_official:
                ent['officialErr'] = str(o)[:150]
            res['blocks'][b] = ent
        if (i // 10) % 50 == 0:
            print(tag, i, len(blocks), len(res['errors']), flush=True); json.dump(res, open(out, 'w'))
scan(pmblocks, 'pm', True)
scan(randblocks, 'random', True)
res['clientVersionEnd'] = {R: rpc(R, 'web3_clientVersion', []), O: rpc(O, 'web3_clientVersion', [])}
json.dump(res, open(out, 'w'))
print('done', len(res['blocks']), len(res['errors']))
