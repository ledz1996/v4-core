# Read-only eth_call reads on Ethereum of the dispute game setup of Celo, X Layer and Base.
import json, sys, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
RPC = 'https://ethereum-rpc.publicnode.com'
def sel(sig): return keccak(sig.encode())[:4].hex()
def raw(m, p):
    r = urllib.request.Request(RPC, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=30))
def call(to, sig, args='', blk='latest'):
    r = raw('eth_call', [{'to': to, 'data': '0x' + sel(sig) + args}, blk])
    return r.get('result', 'ERR:' + json.dumps(r.get('error')))
def u(x): return '%064x' % x
def addr(x): return '0x' + x[-40:] if x and x.startswith('0x') and len(x) >= 66 else x
def s(x):
    try:
        b = bytes.fromhex(x[2:]); n = int.from_bytes(b[32:64], 'big'); return b[64:64 + n].decode()
    except Exception: return x
blk = int(raw('eth_blockNumber', [])['result'], 16)
B = hex(blk)
out = {'ethBlock': blk, 'chains': {}}
CH = {'42220': {'portal': '0xc5c5D157928BDBD2ACf6d0777626b6C75a9EAEDC', 'dgf': '0xFbAC162162f4009Bb007C6DeBC36B1dAC10aF683'},
      '196': {'portal': None, 'dgf': '0x9D4c8FAEadDdDeeE1Ed0c92dAbAD815c2484f675'},
      '8453': {'portal': None, 'dgf': '0x43edb88c4b80fdd2adff2412a7bebf9df42cb40e'}}
GETTERS = ['version()', 'gameType()', 'absolutePrestate()', 'vm()', 'aggregationVkey()', 'rangeVkeyCommitment()', 'rollupConfigHash()',
           'sp1Verifier()', 'verifier()', 'accessManager()', 'anchorStateRegistry()', 'challengerBond()', 'maxChallengeDuration()', 'maxProveDuration()',
           'teeImageHash()', 'zkRangeHash()', 'zkAggregateHash()', 'TEE_IMAGE_HASH()', 'ZK_RANGE_HASH()', 'ZK_AGGREGATE_HASH()', 'teeVerifier()', 'zkVerifier()',
           'proposer()', 'challenger()', 'l2ChainId()', 'status()', 'rootClaim()', 'l2SequenceNumber()', 'l2BlockNumber()', 'gameCreator()', 'challengedBy()', 'wasRespectedGameTypeWhenCreated()']
for cid, c in CH.items():
    r = {'dgf': c['dgf'], 'dgfVersion': s(call(c['dgf'], 'version()', blk=B))}
    if c['portal']:
        r['portal'] = c['portal']
        r['portal.respectedGameType()'] = call(c['portal'], 'respectedGameType()', blk=B)
        r['portal.anchorStateRegistry()'] = call(c['portal'], 'anchorStateRegistry()', blk=B)
        r['portal.version()'] = s(call(c['portal'], 'version()', blk=B))
        asr = addr(r['portal.anchorStateRegistry()'])
        if asr and not asr.startswith('ERR'):
            r['asr.respectedGameType()'] = call(asr, 'respectedGameType()', blk=B)
    cnt = int(call(c['dgf'], 'gameCount()', blk=B), 16); r['gameCount'] = cnt
    types = {}
    for i in range(cnt - 1, max(cnt - 40, -1), -1):
        g = call(c['dgf'], 'gameAtIndex(uint256)', u(i), B); b = bytes.fromhex(g[2:])
        gt = int.from_bytes(b[0:32], 'big'); proxy = '0x' + b[76:96].hex(); ts = int.from_bytes(b[32:64], 'big')
        types.setdefault(gt, []).append({'index': i, 'proxy': proxy, 'timestamp': ts})
    r['recentGameTypes'] = {k: len(v) for k, v in types.items()}
    r['types'] = {}
    for gt, games in types.items():
        impl = addr(call(c['dgf'], 'gameImpls(uint32)', u(gt), B))
        t = {'impl': impl, 'gameArgs': call(c['dgf'], 'gameArgs(uint32)', u(gt), B), 'initBonds': call(c['dgf'], 'initBonds(uint32)', u(gt), B), 'newest': games[0]}
        t['implGetters'] = {}
        for f in GETTERS:
            v = call(impl, f, blk=B)
            if v and not v.startswith('ERR') and v != '0x': t['implGetters'][f] = s(v) if f == 'version()' else v
        t['gameGetters'] = {}
        for f in GETTERS:
            v = call(games[0]['proxy'], f, blk=B)
            if v and not v.startswith('ERR') and v != '0x': t['gameGetters'][f] = s(v) if f == 'version()' else v
        r['types'][gt] = t
    out['chains'][cid] = r
    print(cid, json.dumps(r, indent=1)[:6000], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
