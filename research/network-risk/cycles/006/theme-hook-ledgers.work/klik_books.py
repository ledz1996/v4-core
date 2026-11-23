# Ethereum KlikLauncher 0xb6da931d: compare the creator fee ledger with what the factory received and paid in SPCXon. Read-only eth_getLogs.
import sys, collections
from common import *
sys.path.insert(0, C5)
from fetch import getlogs_range
u = 'https://mainnet.gateway.tenderly.co'; u2 = 'https://ethereum-rpc.publicnode.com'
fac = '0xb6da931df2ed2c80db47923d4eb46fd913ee01c3'; hook = '0x1d06faa7ff674ccfd8a5736c0c0973cb0a8fa0cc'; SPCX = '0xc9eef266834730340a55b6cc24621b31baf55581'
head = int(rpc(u2, 'eth_blockNumber', []), 16)
logs = []
getlogs_range(u, {'address': fac}, 25800000, head, 50000, workers=3, on_logs=lambda r: logs.extend(r))
T_CRED = '0x' + keccak256(b'CreatorFeeCredited(address,uint256)').hex(); T_COLL = '0x' + keccak256(b'FeesCollected(address,address,uint256)').hex(); T_LAUNCH = '0x' + keccak256(b'Launched(address,address,address)').hex()
print('factory logs', len(logs), 'first block', min(int(l['blockNumber'], 16) for l in logs) if logs else None, collections.Counter(l['topics'][0][:10] for l in logs).most_common(8), T_CRED[:10], T_COLL[:10])
cred = collections.Counter(); coll = collections.Counter(); toks = set()
for l in logs:
    t = l['topics']
    if t[0] == T_CRED: tok = '0x' + (t[1][-40:] if len(t) > 1 else l['data'][26:66]); amt = int(l['data'][-64:], 16); cred[tok] += amt; toks.add(tok)
    if t[0] == T_COLL: tok = '0x' + t[1][-40:]; amt = int(l['data'][-64:], 16); coll[tok] += amt; toks.add(tok)
toks = sorted(toks)
res = mc3(u2, [(fac, sel('pairOf(address)')[2:] + adr(t)) for t in toks] + [(fac, sel('creatorFees(address)')[2:] + adr(t)) for t in toks])
pair = {t: '0x' + res[i][1][-40:] for i, t in enumerate(toks)}; owed = {t: int(res[len(toks) + i][1][:64], 16) for i, t in enumerate(toks)}
byp = collections.defaultdict(lambda: [0, 0, 0, 0])
for t in toks:
    p = pair[t]; byp[p][0] += cred[t]; byp[p][1] += coll[t]; byp[p][2] += owed[t]; byp[p][3] += 1
tl = []
getlogs_range(u, {'address': SPCX, 'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', None, pad_addr(fac)]}, 25800000, head, 50000, workers=3, on_logs=lambda r: tl.extend(r))
inn = sum(int(l['data'], 16) for l in tl); src = collections.Counter('0x' + l['topics'][1][-40:] for l in tl)
tl2 = []
getlogs_range(u, {'address': SPCX, 'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', pad_addr(fac)]}, 25800000, head, 50000, workers=3, on_logs=lambda r: tl2.extend(r))
out = sum(int(l['data'], 16) for l in tl2)
bal = int(call(u2, SPCX, 'balanceOf(address)', adr(fac)), 16)
print('SPCXon pair: tokens', byp[SPCX][3], 'credited', byp[SPCX][0], 'collected', byp[SPCX][1], 'still owed (creatorFees)', byp[SPCX][2])
print('SPCXon transfers into factory', inn, 'from', dict(src), 'out of factory', out, 'balance now', bal, 'block', head)
for p, v in sorted(byp.items(), key=lambda kv: -kv[1][3])[:8]: print('  pair', p, 'tokens', v[3], 'credited', v[0], 'collected', v[1], 'owed', v[2])
json.dump(dict(block=head, spcx=dict(tokens=byp[SPCX][3], credited=str(byp[SPCX][0]), collected=str(byp[SPCX][1]), owed=str(byp[SPCX][2]), transfersIn=str(inn), transfersOut=str(out), balance=str(bal))), open(os.path.join(RAW, 'klik_books_1.json'), 'w'))
hk = sum(int(l['data'], 16) for l in tl if l['topics'][1][-40:] == hook[2:])
print('SPCXon from hook to factory', hk, 'credited to SPCXon paired tokens', byp[SPCX][0], 'difference', byp[SPCX][0] - hk)
# which credits had no matching SPCXon transfer in the same transaction
tx_in = collections.Counter()
for l in tl:
    if l['topics'][1][-40:] == hook[2:]: tx_in[l['transactionHash']] += int(l['data'], 16)
tx_cr = collections.Counter(); tx_tok = collections.defaultdict(set)
for l in logs:
    t = l['topics']
    if t[0] == T_CRED:
        tok = '0x' + (t[1][-40:] if len(t) > 1 else l['data'][26:66])
        if pair.get(tok) == SPCX: tx_cr[l['transactionHash']] += int(l['data'][-64:], 16); tx_tok[l['transactionHash']].add(tok)
mis = [(h, v, tx_in.get(h, 0), sorted(tx_tok[h])) for h, v in tx_cr.items() if tx_in.get(h, 0) != v]
print('transactions where the SPCXon credit differs from the SPCXon the hook sent:', len(mis), 'credit sum', sum(m[1] for m in mis), 'received sum', sum(m[2] for m in mis))
for m in sorted(mis, key=lambda m: -(m[1] - m[2]))[:8]: print('  ', m)
# other pairs: owed against balance
ps = [p for p in byp if int(p, 16)]
r = mc3(u2, [(p, '70a08231' + adr(fac)) for p in ps])
for p, (ok, b) in zip(ps, r):
    print('  pair', p, 'owed', byp[p][2], 'factory balance', int(b[:64], 16) if ok and len(b) >= 64 else None)
json.dump(dict(block=head, hookToFactory=str(hk), mismatches=[(m[0], str(m[1]), str(m[2]), m[3]) for m in mis][:50], pairs={p: dict(owed=str(byp[p][2]), credited=str(byp[p][0]), collected=str(byp[p][1])) for p in byp}), open(os.path.join(RAW, 'klik_books_1b.json'), 'w'))
