# Who may propose or challenge, read by eth_call on Ethereum.
import json, sys
sys.argv = sys.argv[:2]
exec(open('/home/user/v4-core/research/network-risk/cycles/013/theme-proof-builds-2.work/celo/dgf.py').read().split('blk = int')[0])
blk = int(raw('eth_blockNumber', [])['result'], 16); B = hex(blk)
Z = u(0)
out = {'ethBlock': blk}
for name, am in {'celo42': '0x2c4e8f333224139193790fb27fc99b926061d889', 'xlayer1961': '0xb0998d01ef27caef56e264c976e5b9e1d2847ccb', 'xlayer42': '0x98ba64d8c8dd33bd75f2154214bfd849d0d5c17b'}.items():
    r = {}
    for f in ['proposers(address)', 'challengers(address)', 'isAllowedProposer(address)', 'isAllowedChallenger(address)']:
        r[f + '[0x0]'] = call(am, f, Z, B)
    for f in ['FALLBACK_TIMEOUT()', 'getLastProposalTimestamp()', 'owner()', 'DISPUTE_GAME_FACTORY()']:
        r[f] = call(am, f, '', B)
    out[name] = r
for asr in ['0xaa45411f6a990b6549a1effdd23c3a51de918832', '0x000590bb65ab1864a7ad46d6b957cc9a4f2c149d', '0x909f6cf47ed12f010a796527f562bfc26c7f4e72']:
    out['asr ' + asr] = {f: call(asr, f, '', B) for f in ['respectedGameType()', 'version()', 'portal()', 'disputeGameFactory()', 'getAnchorRoot()']}
    out['asr ' + asr]['version()'] = s(out['asr ' + asr]['version()'])
print(json.dumps(out, indent=1)); json.dump(out, open(sys.argv[1], 'w'), indent=1)
