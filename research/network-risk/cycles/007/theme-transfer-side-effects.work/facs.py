# Step 2b. v2 style and v3 style factories per network. Candidates come from the Uniswap deployment pages (fetched), from factory()
# of the pairs that pooled tokens name themselves (getters_*.json.gz), and from a hand list. Each one is kept only when it answers
# allPairsLength() or allPoolsLength() on chain with a number above zero (v2 style) or feeAmountTickSpacing(3000) = 60 / (2500) = 50 (v3 style).
import sys, json, os, collections
from base import *
UNI_V2 = {1: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f', 130: '0x1f98400000000000000000000000000000000002', 42161: '0xf1D7CC64Fb4452F05c498126312eBE29f30Fbcf9', 43114: '0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C',
          56: '0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6', 8453: '0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6', 10: '0x0c3c1c532F1e39EdF36BE9Fe0bE1410313E074Bf', 137: '0x9e5A52f57b3038F1B8EeE45F28b3C1967e22799C',
          7777777: '0x0F797dC7efaEA995bB916f268D919d0a1950eE3C', 480: '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f', 143: '0x182a927119d56008d921126764bf884221b10f59', 196: '0xDf38F24fE153761634Be942F9d859f3DBA857E95',
          4326: '0xbf56488c857a881ae7e3bed27cf99c10a7ab7e50', 4217: '0xf9ec577a4e45b5278bb7cf60fcbc20c3acaef68f', 4663: '0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f', 999: '0x89e5DB8B5aA49aA85AC63f691524311AEB649eba',
          99901: '0xBbBcC62853a5fA27b93d6Bab3E6F7ce841E25Df2'}
UNI_V3 = {1: '0x1F98431c8aD98523631AE4a59f267346ea31F984', 8453: '0x33128a8fC17869897dcE68Ed026d694621f6FDfD', 56: '0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7', 42161: '0x1F98431c8aD98523631AE4a59f267346ea31F984',
          10: '0x1F98431c8aD98523631AE4a59f267346ea31F984', 137: '0x1F98431c8aD98523631AE4a59f267346ea31F984', 43114: '0x740b1c1de25031C31FF4fC9A62f554A55cdC1baD', 42220: '0xAfE208a311B21f13EF87E33A90049fC17A7acDEc',
          130: '0x1f98400000000000000000000000000000000003', 7777777: '0x7145F8aeef1f6510E92164038E1B6F8cB2c42Cbb', 143: '0x204faca1764b154221e35c0d20abb3c525710498'}
# hand list, each verified on chain below before use
HAND_V2 = {1: ['0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac', '0x115934131916C8b277DD010Ee02de363c09d037c', '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362'],
           56: ['0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73', '0xBCfCcbde45cE874adCB698cC183deBcF17952812', '0x858E3312ed3A876947EA49d572A7C42DE08af7EE', '0x0841BD0B734E4F5853f0dD8d7Ea041c241fb0Da6',
                '0xc35DADB65012eC5796536bD9864eD8773aBc74C4', '0x86407bEa2078ea5f5EB5A52B2caA963bC1F889Da', '0x3CD1C46068dAEa5Ebb0d3f55F6915B10648062B8', '0x01bF7C66c6BD861915CdaaE475042d3c4BaE16A7'],
           8453: ['0x71524B4f93c58fcbF659783284E38825f0622859', '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB', '0x02a84c1b3BBD7401a5f7fa98a384EBC70bB5749E', '0x3E84D913803b02A4a7f027165E8cA42C14C0FdE7',
                  '0x04C9f118d21e8B767D2e50C946f0cC9F6C367300', '0x1B8128c3A1B7D20053D10763ff02466ca7FF99FC'],
           42161: ['0xc35DADB65012eC5796536bD9864eD8773aBc74C4', '0x6EcCab422D763aC031210895C81787E87B43A652', '0x02a84c1b3BBD7401a5f7fa98a384EBC70bB5749E'],
           137: ['0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32', '0xc35DADB65012eC5796536bD9864eD8773aBc74C4', '0xCf083Be4164828f00cAE704EC15a36D711491284'],
           43114: ['0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10', '0xefa94DE7a4656D787667C749f7E1223D71E9FD88', '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'],
           42220: ['0x62d5b84bE28a183aBB507E125B384122D2C25fAE', '0x79a530c8e2fA8748B7B40dd3629C0520c2cCf03f', '0xc35DADB65012eC5796536bD9864eD8773aBc74C4'],
           10: [], 130: []}
UNI_V2_ROUTER = {1: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', 130: '0x284f11109359a7e1306c3e447ef14d38400063ff', 42161: '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24', 43114: '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24',
                 56: '0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24', 8453: '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24', 10: '0x4A7b5Da61326A6379179b40d00F57E5bbDC962c2', 137: '0xedf6066a2b290C185783862C7F4776A2C8077AD1',
                 7777777: '0xa00F34A632630EFd15223B1968358bA4845bEEC7', 480: '0x541aB7c31A119441eF3575F6973277DE0eF460bd', 143: '0x4b2ab38dbf28d31d467aa8993f6c2585981d6804', 196: '0x182a927119d56008d921126764bf884221b10f59',
                 4326: '0xb73055db2b3a3eae87a331dd88e4a80b43602690', 4217: '0x0fbac3c46f6f83b44c7fb4ea986d7309c701d73e', 4663: '0x89e5db8b5aa49aa85ac63f691524311aeb649eba', 999: '0x1f7d7550B1b028f7571E69A784071F0205FD2EfA',
                 99901: '0xE783DE89a7F0408687f051e3E6D0BEb62719EbAd'}
HAND_SOLIDLY = {8453: ['0x420DD381b31aEf6683db6B902084cB0FFECe40Da'], 10: ['0xF1046053aa5682b4F9a81b5481394DA16BE5FF5a']}
HAND_V3 = {56: ['0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865'], 1: ['0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865'], 8453: ['0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865'], 42161: ['0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865']}
# official deployments file fetched from https://developers.uniswap.org/deployments.json (raw/uniswap_deployments.json)
_dep = json.load(open(os.path.join(RAW7, 'uniswap_deployments.json')))['records']
for _r in _dep:
    if _r.get('env') != 'mainnet': continue
    if _r['contract'] == 'UniswapV2Factory': UNI_V2[_r['chainId']] = _r['address']
    if _r['contract'] == 'UniswapV3Factory': UNI_V3[_r['chainId']] = _r['address']
    if _r['contract'] == 'UniswapV2Router02': UNI_V2_ROUTER[_r['chainId']] = _r['address']
def q(cid, a, data):
    r = ecall(cid, a, data, tries=4)
    return int(r, 16) if isinstance(r, str) and len(r) == 66 else None
def run(cid):
    g = jz(os.path.join(RAW7, 'getters_%d.json.gz' % cid))
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    fac = collections.Counter(r['fac'] for t, rows in g.items() for r in rows if t in (r['t0'], r['t1']) and r['fac'])
    other = collections.Counter((r['t1'] if r['t0'] == t else r['t0']) for t, rows in g.items() for r in rows if t in (r['t0'], r['t1']))
    cands = [(a.lower(), 'uniswap docs') for a in [UNI_V2.get(cid)] if a] + [(a.lower(), 'hand') for a in HAND_V2.get(cid, [])] + [(a, 'named by %d tokens' % n) for a, n in fac.most_common(15)]
    v2 = {}; sol = {}; v3 = {}
    for a, why in cands:
        if a in v2 or a in sol or a in v3: continue
        n = q(cid, a, '0x574f2ba3')
        if n: v2[a] = dict(why=why, pairs=n); continue
        n = q(cid, a, '0xefde4e64')
        if n: sol[a] = dict(why=why, pools=n); continue
        if q(cid, a, '0x22afcccb' + u256(3000)) == 60 or q(cid, a, '0x22afcccb' + u256(2500)) == 50 or q(cid, a, '0x22afcccb' + u256(500)) == 10: v3[a] = dict(why=why)
    for a in HAND_SOLIDLY.get(cid, []):
        n = q(cid, a.lower(), '0xefde4e64')
        if n: sol[a.lower()] = dict(why='hand', pools=n)
    for a, why in [(UNI_V3.get(cid), 'uniswap docs')] + [(x, 'hand') for x in HAND_V3.get(cid, [])]:
        if not a: continue
        a = a.lower()
        fees = [f for f, ts in ((100, 1), (500, 10), (2500, 50), (3000, 60), (10000, 200)) if q(cid, a, '0x22afcccb' + u256(f)) == ts]
        if fees: v3[a] = dict(why=why, fees=fees)
    for a in v3:
        if 'fees' not in v3[a]: v3[a]['fees'] = [f for f, ts in ((100, 1), (500, 10), (2500, 50), (3000, 60), (10000, 200)) if q(cid, a, '0x22afcccb' + u256(f)) == ts]
    top = sorted(live, key=lambda t: -live[t]['usd'] if live[t]['usd'] < 1e12 else 0)[:8]
    bases = []
    wn = None
    if cid in UNI_V2_ROUTER:
        v = q(cid, UNI_V2_ROUTER[cid].lower(), '0xad5c4648')
        if v: wn = '0x%040x' % v; bases.append(wn)
    for t in [a for a, n in other.most_common(6) if a] + top:
        if t not in bases: bases.append(t)
    out = dict(chainId=cid, wrappedNative=wn, v2=v2, solidly=sol, v3=v3, bases=bases, baseSyms=[live.get(b, {}).get('sym') for b in bases])
    json.dump(out, open(os.path.join(RAW7, 'facs_%d.json' % cid), 'w'), indent=1)
    print(cid, net(cid)['name'], 'v2', {a[:10]: v.get('pairs') for a, v in v2.items()}, 'solidly', {a[:10]: v.get('pools') for a, v in sol.items()}, 'v3', {a[:10]: v['fees'] for a, v in v3.items()}, 'bases', out['baseSyms'], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
