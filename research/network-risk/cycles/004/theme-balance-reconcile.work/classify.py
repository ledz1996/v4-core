# Classify every token that did not reconcile. Rules are symbol patterns for lending receipt tokens and wrapped natives,
# and a table of addresses that were read one by one (source on Sourcify, selectors, or on-chain state).
import json, glob, re, os
MAN = {
 # address: (class, trigger, note)
 '0x99a57e6c8558bc6689f894e068733adf83c19725': ('rebase up, public trigger', 'public', 'sLGNS: Staking.rebase() has no caller check'),
 '0xb0c22d8d350c67420f06f48936654f567c73e8c8': ('rebase up, public trigger', 'public', 'sKLIMA: KlimaStaking.rebase() has no caller check; simulated'),
 '0x2f712578fbd1c42c3459b67dd2b9035e994bbc93': ('rebase up, public trigger', 'public', 'sATH: staking exposes rebase(); epoch not due at the time of the test'),
 '0x2a54ba2964c8cd459dc568853f79813a60761b58': ('rebase up, public trigger', 'public', 'USDI: VaultController.calculateInterest() callable by anyone; simulated'),
 '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': ('rebase by role', 'role', 'stETH, covered by F-012'),
 '0x35fa164735182de50811e8e2e824cfb9b6118ac2': ('rebase by role', 'role', 'eETH'),
 '0x8238884ec9668ef77b90c6dff4d1a9f4f4823bfe': ('rebase by role', 'role', 'USDO'),
 '0xaf37c1167910ebc994e266949387d2c7c326b879': ('rebase by role', 'role', 'rUSDY'),
 '0xc9e3df3d230980b45adc623c81c3df4a73a5350f': ('rebase by role', 'role', 'USD+'),
 '0x476ef9ac6d8673e220d0e8bc0a810c2dc6a2aa84': ('share rate that follows another contract', 'role', 'USPD: rate contract follows the stETH rate'),
 '0xe575cc6ec0b5d176127ac61ad2d3d9d19d1aa4a0': ('share rate that follows another contract', 'donation only', 'stkWALLET: shareValue of the staking pool'),
 '0x5ab22e9c360807f16dfa34ad5c589055d2871a5b': ('lending receipt, grows with time', 'none', 'Wildcat market token, scale factor'),
 '0x11fb7c5e6fe7e42fb9e28929b673d3eee20048d4': ('rebase down by time', 'none', 'TURING: daily decay'),
 '0x73eb4a9db8d8c7539ba5701cf1cdd3452038970b': ('rebase up by time', 'none', '666: index grows 33 percent per day for 200 days'),
 '0xda7700bfd540f8b22441ca0d000e91ac54b74456': ('rebase up by time', 'none', 'EXPT2: unverified, balance grows with time'),
 '0xe8cc6950f3e32d30e706fef13197b44a6fc78b11': ('rebase up by time', 'none', 'EXPT: unverified, balance grows with time'),
 '0x0d6b6f604c1bf5b3533c445334bb4e1044145688': ('rebase down by time', 'none', 'SMK2: epoch index'),
 '0xd07d35368e04a839dee335e213302b21ef14bb4a': ('other', 'unknown', 'CRYSTAL: token and NFT hybrid, 0.07 tokens held'),
 '0xffcfe05d6fe5a554ed668225eadbef3be130d28f': ('rebase down by time', 'none', 'DDL: burn and dividend token, 3.3 tokens held'),
 '0xd6b7e841762e243147a834bd733feed492d9c5c8': ('rebase up by time', 'unknown', 'TKN: unverified test token, 2 tokens held'),
 '0xf377330b2568e9db23a4fbd03cada203eb96a339': ('rebase up by time', 'unknown', 'TKN: unverified test token, 2 tokens held'),
 '0x15dd62f6d41cdf53728136216c372630adbc3282': ('other', 'unknown', 'TKN: 7 base units'),
 '0xa2b4c0af19cc16a6cfacce81f192b024d625817d': ('reflection', 'any transfer by anyone, at the sender\'s cost', 'KISHU'),
 '0xf24cd72b0f094d8a0e7cc48914d1d24b9e369142': ('reflection', 'any transfer by anyone, at the sender\'s cost', '#GMM'),
 '0xfafce4f694ef507639cc2b63794f1fcbc2deffa7': ('reflection', 'any transfer by anyone, at the sender\'s cost', 'HKU: dividend shares'),
 '0x0b4d676eebf9bf99a70da085e1d2381190f7d3bb': ('reflection', 'any transfer by anyone, at the sender\'s cost', 'Share'),
 '0x74f84a0add717a6c405b2c8c0b82d94b514e113e': ('reflection', 'any transfer by anyone, at the sender\'s cost', 'BRTM'),
 '0xc17c30e98541188614df99239cabd40280810ca3': ('fee on transfer', 'none', 'RISE: recipient receives less than the amount that leaves the PoolManager'),
 '0x3231cb76718cdef2155fc47b5286d82e6eda273f': ('second address of one ledger', 'none', 'EURe v1 address, same balance as 0x39b8b6385416f4ca36a20319f70d28621895279d'),
 '0x18ec0a6e18e5bc3784fdd3a3634b31245ab704f6': ('second address of one ledger', 'none', 'EURe v1 address, same balance as 0xe0aea583266584dafbb3f9c3211d5588c73fea8d'),
 '0x4f95c5ba0c7c69fb2f9340e190ccee890b3bd87c': ('second address of one ledger', 'none', 'Frax custodian: balanceOf returns the frxUSD balance'),
 '0x0000000000000000000000000000000000001010': ('second address of one ledger', 'none', 'POL system token mirrors the native balance, covered by F-008'),
 '0x3600000000000000000000000000000000000000': ('second address of one ledger', 'none', 'Arc USDC is the ERC-20 face of the native balance'),
 '0xfffffffffffffffffffffffffffffffffffffffe': ('system log emitter', 'none', 'Arc emits native transfer logs from this address'),
 '0x20204018a5a97149168faa73477bd5db9756a141': ('spoofed logs', 'none', 'look-alike USDC that logs transfers it does not make'),
 '0x0ae7cd10f94fd16a6f9a29a372708718144c46f8': ('rebase up, public trigger', 'public', 'sSAC: staking exposes rebase(); epoch not due at the time of the test'),
 '0x6d6c16a3cbd318f3000e33cfd27662cf00f7e7c1': ('rebase up, public trigger', 'public', 'sNVB: StakingV2.rebase() callable by anyone; simulated'),
 '0x1a9be135c946acee25f28d09173b2adceb5da604': ('fee or reflection token, source not read', 'unknown', 'DRP'),
 '0x7c63f96feafacd84e75a594c00fac3693386fbf0': ('fee or reflection token, source not read', 'unknown', 'ASS'),
 '0xa57ac35ce91ee92caefaa8dc04140c8e232c2e50': ('fee or reflection token, source not read', 'unknown', 'PIT'),
 '0xe4fae3faa8300810c835970b9187c268f55d998f': ('fee or reflection token, source not read', 'unknown', 'CATE'),
 '0xec6d1444ce527fa92350af62d42eb23182233333': ('fee or reflection token, source not read', 'unknown', 'GFH'),
 '0x36ed877d3bbb868eae4a89d6705e55a3ed2b66dc': ('lending receipt, grows with time', 'none', 'aAstarASTR'),
 '0x53e240c0f985175da046a62f26d490d1e259036e': ('lending receipt, grows with time', 'none', 'Seamless sUSDC'),
 '0xb4f8a17e9917a7dd45c3726041bcd3848c5c2e94': ('lending receipt, grows with time', 'none', 'ExtraFi exOptOP'),
}
TURING = 'TURING'; PYRE = 'PYRE'
LEND = re.compile(r'^(a(Eth|Opt|Arb|Pol|Ava|Bas|Bnb|Mon|Meg|Ink|Sone|Cel|Astar|Hor|Amm)|a[A-Z][A-Za-z.]*$|am[A-Z]|av[A-Z]|sp[A-Zwr]|r(USDT|USDC|WETH|DAI|wstETH)$|rz|m(CELO|CREAL)$|n(WETH|USDC|USDT0|AUSD|WMON)$|c[A-Za-z]+v3$|DP[A-Z])')
def cls(r):
    a = r['token']; s = (r.get('symbol') or '')
    if a in MAN: return MAN[a]
    if s == TURING: return ('rebase down by time', 'none', 'TURING: daily decay')
    if s == PYRE: return ('rebase down by time', 'none', 'PYRE: decay index')
    if s in ('WETH', 'WMON', 'WBNB'): return ('wrapped native credited through Deposit events', 'none', 'reconciles once Deposit logs with the PoolManager as destination are added')
    if s.endswith('x') and abs(int(r['diff'])) < 1000: return ('share rate, rounding of a few base units', 'role', 'xStocks token with a multiplier set by the issuer')
    if LEND.match(s): return ('lending receipt, grows with time', 'none', '')
    return ('unclassified', 'unknown', '')
out = {}
for fn in sorted(glob.glob('raw/mismatch_*.json')):
    if '_7d' in fn: continue
    o = json.load(open(fn)); cid = o['chainId']; rows = []
    for r in o['rows']:
        if r['status'] != 'mismatch': continue
        c, trig, note = cls(r); v = r.get('v') or {}
        d = r.get('decimals') or 0
        rows.append(dict(token=r['token'], symbol=r.get('symbol'), decimals=d, bal1=r['bal1'], bal2=r['bal2'], tin=r['tin'], tout=r['tout'], nlogs=r['nlogs'], diff=r['diff'],
                         diffAfterDepositLogs=v.get('diffAfterWrap'), verifiedSecondRead=v.get('sameAsFirstPass'), cls=c, trigger=trig, note=note,
                         balHuman=int(r['bal2']) / 10 ** d, diffHuman=int(r['diff']) / 10 ** d))
    out[cid] = dict(name=o['name'], B1=o['B1'], B2=o['B2'], seconds=o['seconds'], universe=o['universe'], counts=o['counts'], rows=rows)
json.dump(out, open('raw/classified.json', 'w'), indent=1)
for cid, o in out.items():
    by = {}
    for r in o['rows']: by.setdefault(r['cls'], []).append(r)
    print('==', cid, o['name'], 'universe', o['universe'], o['counts'])
    for c, rs in by.items():
        rs.sort(key=lambda r: -abs(r['balHuman']))
        print('   %-48s %3d  %s' % (c, len(rs), ', '.join('%s %.4g (%+.3g)' % (r['symbol'], r['balHuman'], r['diffHuman']) for r in rs[:6])))
