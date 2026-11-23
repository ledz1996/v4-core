# One rule for every flagged row (transaction, token) of the transfer census, no labels. Read-only:
# eth_getTransactionReceipt, eth_getLogs on one block, eth_call at two blocks, debug_traceTransaction (callTracer) where served.
#   b0, b1  balanceOf(PoolManager) one block before and at the block
#   S       sum of Transfer logs of the token in that block into the PoolManager minus out of it (wrapper Deposit logs count as in)
#   resid   (b1 - b0) - S : balance change of the block that no Transfer log explains
#   trace   calls PoolManager -> token.transfer (takes), sync, settle and their results, and the calls made between sync and settle
# Classes:
#   spoof    the balance did not change (resid cancels the logged outflow) and the PoolManager made no transfer call to the token
#   surplus  the PoolManager paid the amount by take and settle credited a rise of balanceOf since sync that no Transfer log carries
#   fees     collectProtocolFees was called (controller path, src/ProtocolFees.sol:44-57)
#   open     anything else: the balance fell, or the payout has no credit that the trace or the logs show
import json, time
from lib import *
from config import CFG
from common import EXTRA
SEL = {sel(s): s.split('(')[0] for s in ['sync(address)', 'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'mint(address,uint256,uint256)',
       'burn(address,uint256,uint256)', 'unlock(bytes)', 'collectProtocolFees(address,address,uint256)', 'clear(address,uint256)']}
DEPOSIT = '0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c'
T6909 = '0x1b3d7edb2e9c0b0e7c525b20aaaef0f5940d2ed71663c7d39266ecafac728859'
POOLEV = {'0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f': 'Swap', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec': 'ModifyLiquidity',
          '0x29ef05caaff9404b7cb6d1c0e9bbae9eaa7ab2541feba1a9c4248594c08156cb': 'Donate'}
ARCH = {56: ['https://bsc.api.pocket.network', 'https://bsc.rpc.sentio.xyz', 'https://bsc-mainnet.public.blastapi.io'],
        480: ['https://sparkling-autumn-dinghy.worldchain-mainnet.quiknode.pro', 'https://worldchain-mainnet.g.alchemy.com/public'],
        196: ['https://rpc.xlayer.tech', 'https://xlayerrpc.okx.com']}
def state_urls(cid):
    out = []
    for u in ARCH.get(cid, []) + CFG[cid]['state'] + [net(cid)['rpc']] + EXTRA.get(cid, []):
        if u not in out: out.append(u)
    return out
_good = {}
def any_rpc(cid, method, params, kind, timeout=60, rounds=4):
    r = None
    for i in range(rounds):
        r = any_rpc1(cid, method, params, kind, timeout)
        if not (isinstance(r, dict) and set(r) == {'error'}): return r
        time.sleep(1.0 + i)
    return r
def any_rpc1(cid, method, params, kind, timeout=60):
    us = state_urls(cid); g = _good.get((cid, kind))
    if g: us = [g] + [u for u in us if u != g]
    last = None
    for u in us:
        for k in range(2):
            try:
                j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}, timeout=timeout, tries=1)
                if 'error' in j:
                    last = json.dumps(j['error'])[:120]
                    if any(s in last.lower() for s in ('rate', 'limit', 'capacity', 'busy', 'too many')): time.sleep(1.5); continue
                    break
                if j.get('result') is None: last = 'null'; break
                _good[(cid, kind)] = u; return j['result']
            except Exception as e:
                last = repr(e)[:120]; time.sleep(0.5)
    return {'error': last}
def bal(cid, tok, who, block):
    r = any_rpc(cid, 'eth_call', [{'to': tok, 'data': sel('balanceOf(address)') + adr(who)}, hex(block)], 'state', timeout=30)
    if isinstance(r, str) and len(r) >= 66: return int(r[:66], 16)
    return None
def walk(c, depth=0, out=None):
    if out is None: out = []
    out.append((depth, c))
    for x in c.get('calls') or []: walk(x, depth + 1, out)
    return out
def read_trace(cid, tx, tok):
    pm = net(cid)['poolManager'].lower(); tok = tok.lower()
    t = any_rpc(cid, 'debug_traceTransaction', [tx, {'tracer': 'callTracer'}], 'trace', timeout=120)
    if not isinstance(t, dict) or 'error' in t and 'calls' not in t and 'to' not in t: return None
    flat = walk(t); takes = []; paid = []; fees = []; trig = []; synced = None; top = dict(sender=t.get('from'), to=t.get('to'), selector=(t.get('input') or '')[:10])
    for d, c in flat:
        if c.get('error'): continue
        to = (c.get('to') or '').lower(); frm = (c.get('from') or '').lower(); inp = c.get('input') or '0x'; s = inp[:10]
        if frm == pm and to == tok and s == '0xa9059cbb' and len(inp) >= 138:
            takes.append(('0x' + inp[34:74], int(inp[74:138], 16)))
        if to == pm and c.get('type') in ('CALL', None) or to == pm:
            nm = SEL.get(s)
            if nm == 'sync': synced = '0x' + inp[34:74]; 
            elif nm in ('settle', 'settleFor'):
                if synced == tok: paid.append(int(c.get('output') or '0x0', 16))
                synced = None
            elif nm == 'collectProtocolFees' and len(inp) >= 202 and inp[98:138] == tok[2:]: fees.append(int(c.get('output') or '0x0', 16))
        elif synced == tok and frm != pm and not (to == tok and s in ('0xa9059cbb', '0x23b872dd', '0x70a08231', '0x095ea7b3', '0xdd62ed3e')) and c.get('type') != 'STATICCALL':
            if len(trig) < 12: trig.append(dict(to=to, selector=s, depth=d))
    return dict(top=top, takes=takes, paid=paid, fees=fees, betweenSyncAndSettle=trig, pmCalled=any((c.get('to') or '').lower() == pm for d, c in flat))
NAT = '0xfffffffffffffffffffffffffffffffffffffffe'; ZERO = '0x' + '0' * 40; ARCUSDC = '0x3600000000000000000000000000000000000000'
def classify_native(cid, tx, rc):
    # native payouts where the chain logs native transfers at 0xff..fe (Arc). Claims of id 0 count one to one; on Arc claims of the
    # USDC face id 0x3600.. count times 10**12 (6 against 18 decimals) and its own Transfer logs repeat the native log.
    pm = net(cid)['poolManager'].lower(); p = pad_addr(pm); block = int(rc['blockNumber'], 16); out = inn = mint = burn = 0; rec = {}; pool = []
    for l in rc['logs']:
        t = l['topics']; a = l['address'].lower()
        if a == NAT and len(t) == 3 and t[0] == TRANSFER:
            v = int(l['data'][:66], 16)
            if t[1] == p: out += v; rec['0x' + t[2][-40:]] = rec.get('0x' + t[2][-40:], 0) + v
            if t[2] == p: inn += v
        elif a == pm and t and t[0] in POOLEV: pool.append(POOLEV[t[0]])
        elif a == pm and t and t[0] == T6909 and len(t) == 4:
            i = int(t[3], 16); sc = 1 if i == 0 else 10 ** 12 if (cid == 5042 and i == int(ARCUSDC, 16)) else 0
            amt = int(l['data'][2:][64:128] or '0', 16) * sc
            if int(t[1], 16) == 0: mint += amt
            elif int(t[2], 16) == 0: burn += amt
    r = dict(tx=tx, token=NAT, block=block, out=str(out), mint=str(mint), burn=str(burn), poolEvents=len(pool), sender=rc.get('from'), txTo=rc.get('to'), native=True)
    r['in'] = str(inn); top = max(rec, key=rec.get) if rec else None; r['recipient'] = top
    def gb(b):
        x = any_rpc(cid, 'eth_getBalance', [pm, hex(b)], 'state', timeout=30)
        return int(x, 16) if isinstance(x, str) else None
    b0 = gb(block - 1); b1 = gb(block); S = None
    lo = any_rpc(cid, 'eth_getLogs', [{'address': NAT, 'topics': [TRANSFER, p], 'fromBlock': hex(block), 'toBlock': hex(block)}], 'logs')
    li = any_rpc(cid, 'eth_getLogs', [{'address': NAT, 'topics': [TRANSFER, None, p], 'fromBlock': hex(block), 'toBlock': hex(block)}], 'logs')
    if isinstance(lo, list) and isinstance(li, list): S = sum(int(l['data'][:66], 16) for l in li) - sum(int(l['data'][:66], 16) for l in lo)
    resid = None if None in (b0, b1, S) else (b1 - b0) - S
    r.update(b0=None if b0 is None else str(b0), b1=None if b1 is None else str(b1), S=None if S is None else str(S), resid=None if resid is None else str(resid))
    net_out = out + mint - inn - burn; r['netOut'] = str(net_out)
    if net_out <= 0 and not pool: r['cls'] = 'balanced'; r['why'] = 'the native payout is matched by claims burned or value paid in the same transaction' + ('' if resid == 0 else '; block residual %s' % resid)
    elif pool: r['cls'] = 'pool'; r['why'] = 'transaction holds pool events; judged by the census arithmetic'
    else: r['cls'] = 'open'; r['why'] = 'native payout larger than value in plus claims burned'
    return r
def classify(cid, tx, tok, block=None, use_trace=True, owed=0):
    pm = net(cid)['poolManager'].lower(); p = pad_addr(pm); tok = tok.lower()
    if tok in (NAT, ZERO):
        rc = any_rpc(cid, 'eth_getTransactionReceipt', [tx], 'rcpt')
        if not isinstance(rc, dict) or 'logs' not in rc: return dict(tx=tx, token=tok, cls='unread', why='no receipt')
        return classify_native(cid, tx, rc)
    rc = any_rpc(cid, 'eth_getTransactionReceipt', [tx], 'rcpt')
    if not isinstance(rc, dict) or 'logs' not in rc: return dict(tx=tx, token=tok, cls='unread', why='no receipt')
    block = int(rc['blockNumber'], 16); out = inn = mint = burn = 0; rec = {}; pool = []
    for l in rc['logs']:
        t = l['topics']; a = l['address'].lower()
        if a == tok and len(t) == 3 and t[0] == TRANSFER and len(l['data']) >= 66:
            v = int(l['data'][:66], 16)
            if t[1] == p: out += v; rec['0x' + t[2][-40:]] = rec.get('0x' + t[2][-40:], 0) + v
            if t[2] == p: inn += v
        elif a == tok and len(t) == 2 and t[0] == DEPOSIT and t[1] == p: inn += int(l['data'][:66], 16)
        elif a == pm and t and t[0] in POOLEV: pool.append(POOLEV[t[0]])
        elif a == pm and t and t[0] == T6909 and len(t) == 4 and t[3][-40:] == tok[2:]:
            amt = int(l['data'][2:][64:128] or '0', 16)
            if int(t[1], 16) == 0: mint += amt
            elif int(t[2], 16) == 0: burn += amt
    r = dict(tx=tx, token=tok, block=block, out=str(out), mint=str(mint), burn=str(burn), poolEvents=len(pool), sender=rc.get('from'), txTo=rc.get('to'))
    r['in'] = str(inn)
    top = max(rec, key=rec.get) if rec else None; r['recipient'] = top; r['recipients'] = len(rec)
    # block level
    S = None
    lg = any_rpc(cid, 'eth_getLogs', [{'address': tok, 'fromBlock': hex(block), 'toBlock': hex(block)}], 'logs')
    if isinstance(lg, list):
        S = 0
        for l in lg:
            t = l['topics']
            if len(t) == 3 and t[0] == TRANSFER and len(l['data']) >= 66:
                v = int(l['data'][:66], 16)
                if t[2] == p: S += v
                if t[1] == p: S -= v
            elif len(t) == 2 and t[0] == DEPOSIT and t[1] == p: S += int(l['data'][:66], 16)
    b0 = bal(cid, tok, pm, block - 1); b1 = bal(cid, tok, pm, block)
    r0 = bal(cid, tok, top, block - 1) if top else None; r1 = bal(cid, tok, top, block) if top else None
    r.update(b0=None if b0 is None else str(b0), b1=None if b1 is None else str(b1), S=None if S is None else str(S), r0=None if r0 is None else str(r0), r1=None if r1 is None else str(r1))
    resid = None if None in (b0, b1, S) else (b1 - b0) - S; r['resid'] = None if resid is None else str(resid)
    tr = read_trace(cid, tx, tok) if use_trace else None; r['trace'] = tr
    net_out = out + mint - inn - burn; excess = net_out - owed; r['owed'] = str(owed); r['excess'] = str(excess)
    if tr is not None:
        tk = sum(a for _, a in tr['takes']); surplus = sum(tr['paid']) - inn
        if tr['fees'] and sum(tr['fees']) >= excess: r['cls'] = 'fees'; r['why'] = 'collectProtocolFees paid %d of the token in this transaction' % sum(tr['fees'])
        elif surplus > 0 and surplus >= excess > 0: r['cls'] = 'surplus'; r['why'] = 'settle credited %d more than was transferred in after sync' % surplus
        elif tk == 0 and not tr['takes'] and mint == 0:
            if resid is not None and resid == 0 and out > 0 and (b1 < b0): r['cls'] = 'open'; r['why'] = 'balance fell and the PoolManager made no transfer call: the token moved the balance itself'
            elif resid is None: r['cls'] = 'spoof'; r['why'] = 'no transfer call from the PoolManager in the trace; balance not read'
            else: r['cls'] = 'spoof'; r['why'] = 'no transfer call from the PoolManager and the logged outflow did not lower the balance'
        elif surplus > 0: r['cls'] = 'surplus+open'; r['why'] = 'settle credited %d without transfer, excess %d' % (surplus, excess)
        elif tk > 0 and out > tk and out - tk >= excess: r['cls'] = 'open'; r['kind'] = 'sender-charge'; r['why'] = 'the token moved %d out of the PoolManager on top of the %d that take sent' % (out - tk, tk)
        else: r['cls'] = 'open'; r['why'] = 'take by the PoolManager without a credit seen in this transaction'
    else:
        f0 = any_rpc(cid, 'eth_call', [{'to': pm, 'data': sel('protocolFeesAccrued(address)') + adr(tok)}, hex(block - 1)], 'state', timeout=30)
        f1 = any_rpc(cid, 'eth_call', [{'to': pm, 'data': sel('protocolFeesAccrued(address)') + adr(tok)}, hex(block)], 'state', timeout=30)
        if isinstance(f0, str) and isinstance(f1, str) and len(f0) >= 66 and len(f1) >= 66: r['feesAccrued'] = [str(int(f0[:66], 16)), str(int(f1[:66], 16))]
        if 'feesAccrued' in r and out > 0 and int(r['feesAccrued'][0]) >= excess > 0 and int(r['feesAccrued'][1]) < int(r['feesAccrued'][0]):
            r['cls'] = 'fees'; r['why'] = 'no trace; protocolFeesAccrued of the token fell by at least the amount in this block, which only collectProtocolFees does (src/ProtocolFees.sol:52-54)'
        elif resid is None: r['cls'] = 'unread'; r['why'] = 'no trace and no old state'
        elif resid == 0: r['cls'] = 'open'; r['why'] = 'no trace; the balance moved as the logs say'
        elif resid > 0 and b0 > 0 and r0 is not None and r1 is not None and r1 > r0: r['cls'] = 'surplus?'; r['why'] = 'no trace; balance did not fall, recipient gained, PoolManager held a balance'
        elif resid > 0: r['cls'] = 'spoof'; r['why'] = 'no trace; the balance did not change by the logged outflow' + ('' if (r0 is None or r1 is None or r1 <= r0) else ' (recipient gained, PoolManager balance was zero before)')
        else: r['cls'] = 'open'; r['why'] = 'no trace; balance fell by more than the logs say'
    return r
if __name__ == '__main__':
    import sys
    print(json.dumps(classify(int(sys.argv[1]), sys.argv[2], sys.argv[3]), indent=1))
