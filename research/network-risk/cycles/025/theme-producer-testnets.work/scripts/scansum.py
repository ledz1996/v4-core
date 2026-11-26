"""Summarise batchscan/slowscan jsonl files: covered block ranges, failed ranges, clients, logs per address and event.
usage: scansum.py out.json file.jsonl...   (Transfer split into mint, burn and both-nonzero)"""
import sys, json, collections
N = {'0x40e9cecb':'Swap','0xf208f491':'ModifyLiquidity','0xdd466e67':'Initialize','0x29ef05ca':'Donate','0x1b3d7edb':'Transfer','0xb3fd5071':'Approval','0xceb576d9':'OperatorSet','0x8be0079c':'OwnershipTransferred','0xe9c42593':'ProtocolFeeUpdated','0xb4bd8ef5':'ProtocolFeeControllerUpdated'}
Z = '0x' + '0' * 64
res = {}
for f in sys.argv[2:]:
    rngs = []; fails = []; cl = []; c = collections.Counter(); tx = set(); ex = collections.defaultdict(list)
    for l in open(f):
        r = json.loads(l)
        if r.get('done'):
            rngs.append((r['from'], r['to']))
            for x in r['logs']:
                n = N.get(x['topics'][0][:10], x['topics'][0])
                if n == 'Transfer': n = 'Transfer-mint' if x['topics'][1] == Z else ('Transfer-burn' if x['topics'][2] == Z else 'Transfer-bothNonzero')
                c[(x['address'].lower(), n)] += 1; tx.add(x['transactionHash'])
                if n not in ('Swap', 'ModifyLiquidity', 'Transfer-mint', 'Transfer-burn') and len(ex[n]) < 20: ex[n].append([int(x['blockNumber'], 16), x['transactionHash']])
        elif 'failed' in r: fails.append(r)
        elif 'client' in r: cl.append(r)
    rngs.sort(); merged = []
    for a, b in rngs:
        if merged and a <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    res[f] = {'covered': merged, 'blocks': sum(b - a + 1 for a, b in merged), 'failed': fails, 'clients': cl,
              'logs': {'%s|%s' % k: v for k, v in sorted(c.items())}, 'txs': len(tx), 'examples': ex}
    print(f, merged, res[f]['blocks'], len(fails), dict(collections.Counter(k[1] for k in c.elements())))
json.dump(res, open(sys.argv[1], 'w'), indent=1)
