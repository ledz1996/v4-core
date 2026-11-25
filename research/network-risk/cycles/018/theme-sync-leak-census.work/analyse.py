"""Summarise census jsonl files: per network, transactions traced, frames by kind, settle outputs checked against
the source's transient model, transactions that end successfully with an ERC-20 still synced, and for each of those
every later transaction of the same block in the set that calls settle, settleFor or take.
Usage: analyse.py <out.json> <chainId>=<file>[,<file>...] ..."""
import sys, json, collections
Z = '0x' + '0' * 40
res = {}
for arg in sys.argv[2:]:
    cid, files = arg.split('='); rows = {}
    for fn in files.split(','):
        for line in open(fn):
            j = json.loads(line)
            if 'fail' in j:
                rows.setdefault(j['tx'], j); continue
            rows[j['tx']] = j
    ok = [r for r in rows.values() if 'fail' not in r]
    fails = [r['tx'] for r in rows.values() if 'fail' in r]
    st = collections.Counter(); bad = []; leaks = []
    byblock = collections.defaultdict(list)
    for r in ok:
        byblock[r['block']].append(r)
        st['traced'] += 1; st['succeeded' if r['ok'] else 'failedTx'] += 1
        for f in r['frames']:
            st['frame:' + f[0] + (':reverted' if f[3] else '')] += 1
            if f[0] == 'sync' and not f[3]: st['sync:native' if f[1] == Z else 'sync:erc20'] += 1
        st['settleChecks'] += r['settleChecks']
        if r['bad']: bad.append({'tx': r['tx'], 'block': r['block'], 'bad': r['bad'], 'frames': r['frames']})
        if r['ok'] and r['endSynced'] and r['endSynced'] != Z: leaks.append(r)
    pairs = []
    for r in leaks:
        later = [x for x in byblock[r['block']] if x['idx'] > r['idx'] and x['ok'] and any(f[0] in ('settle', 'settleFor', 'take') and not f[3] for f in x['frames'])]
        later_first_own = []
        for x in later:
            seen_sync = False; first = None
            for f in x['frames']:
                if f[3]: continue
                if f[0] == 'sync': seen_sync = True
                if f[0] in ('settle', 'settleFor'):
                    first = 'after own sync' if seen_sync else 'no own sync before it'; break
            later_first_own.append({'tx': x['tx'], 'idx': x['idx'], 'firstSettle': first, 'settleMismatch': bool(x['bad'])})
        pairs.append({'tx': r['tx'], 'block': r['block'], 'idx': r['idx'], 'from': r['from'], 'to': r.get('to'), 'synced': r['endSynced'],
                      'frames': r['frames'], 'laterSameBlock': later_first_own})
    blocks = sorted(byblock)
    res[cid] = {'stats': dict(st), 'traceFailures': fails, 'blocks': [blocks[0], blocks[-1]] if blocks else None, 'nBlocks': len(blocks),
                'blocksWithSeveral': sum(1 for v in byblock.values() if len(v) > 1), 'settleMismatches': bad, 'endsSyncedErc20': pairs}
    print(cid, dict(st), 'fails', len(fails), 'mismatch', len(bad), 'leaks', len(pairs), 'laterSettles', sum(len(p['laterSameBlock']) for p in pairs))
json.dump(res, open(sys.argv[1], 'w'), indent=1)
