import json, glob, os, collections
NETS = [n['chainId'] for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']]
T = {}
for cid in NETS:
    c = json.load(open('raw/census_%d.json' % cid))
    row = {'pools': c['pools'], 'hooks': c['distinctHooks'], 'empty': c['emptyHooks'], 'deleg': c['delegatedHooks'], 'poolsOn': len(c['hookPools']), 'block': c['block'], 'mismatch': len(c['idMismatch']),
           'src': [(s['lo'], s['hi'], s['url']) for s in c['sources']]}
    gatedPools = [p for p in c['hookPools'] if int(p['hook'], 16) & 0x330]
    row['gatedPools'] = len(gatedPools)
    fn = 'raw/detail_%d.json' % cid
    if os.path.exists(fn):
        d = json.load(open(fn))
        row['withLive'] = sum(1 for p in d['pools'] if p['livePositions'])
        row['thirdParty'] = sum(1 for p in d['pools'] if p['thirdPartyLive'])
        row['gatedThird'] = [(p['poolId'][:12], p['hook'], hex(p['flagBits'])) for p in d['pools'] if p['thirdPartyLive'] and p['flagBits'] & 0x330]
        row['tickMismatch'] = sum(1 for p in d['pools'] if p.get('tickCheck', {}).get('mismatch'))
        row['skippedNoTicks'] = len(d.get('skippedNoTicks', []))
    T[cid] = row
    print(cid, {k: v for k, v in row.items() if k != 'src'})
json.dump(T, open('raw/table.json', 'w'), indent=1)
