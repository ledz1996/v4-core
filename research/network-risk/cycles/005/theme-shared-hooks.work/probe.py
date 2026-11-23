# Probe one hook with read-only calls.
#  1. code size, code hash, EIP-1167 / EIP-1967 proxy target
#  2. eth_call PoolManager.initialize from an ordinary account with several PoolKeys that name the hook
#  3. eth_call each flagged callback on the hook with from = PoolManager and a foreign PoolKey
# No transaction is sent. usage: python3 probe.py <chainId> <hook> [...hooks]
import sys, json, gzip, os
from lib import *
from config import CFG
from keccak import keccak256
from summ import flags, load, census
K = '(address,address,uint24,int24,address)'
SIG = dict(
 initialize='initialize(%s,uint160)' % K,
 beforeInitialize='beforeInitialize(address,%s,uint160)' % K,
 afterInitialize='afterInitialize(address,%s,uint160,int24)' % K,
 beforeAddLiquidity='beforeAddLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)' % K,
 afterAddLiquidity='afterAddLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)' % K,
 beforeRemoveLiquidity='beforeRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),bytes)' % K,
 afterRemoveLiquidity='afterRemoveLiquidity(address,%s,(int24,int24,int256,bytes32),int256,int256,bytes)' % K,
 beforeSwap='beforeSwap(address,%s,(bool,int256,uint160),bytes)' % K,
 afterSwap='afterSwap(address,%s,(bool,int256,uint160),int256,bytes)' % K,
 beforeDonate='beforeDonate(address,%s,uint256,uint256,bytes)' % K,
 afterDonate='afterDonate(address,%s,uint256,uint256,bytes)' % K)
SEL = {k: keccak256(v.encode()).hex()[:8] for k, v in SIG.items()}
ERR = {keccak256(s.encode()).hex()[:8]: s for s in ['WrappedError(address,bytes4,bytes,bytes)', 'ManagerLocked()', 'AlreadyUnlocked()', 'PoolAlreadyInitialized()', 'PoolNotInitialized()', 'HookAddressNotValid(address)', 'InvalidHookResponse()', 'HookCallFailed()', 'NotPoolManager()', 'Error(string)', 'Panic(uint256)', 'CurrenciesOutOfOrderOrEqual(address,address)', 'TickSpacingTooLarge(int24)', 'TickSpacingTooSmall(int24)', 'LPFeeTooLarge(uint24)', 'HookNotImplemented()', 'InvalidPool()', 'LockFailure()', 'NotSelf()', 'Unauthorized()', 'OnlyFactory()', 'UnauthorizedDynamicLPFeeUpdate()', 'OwnableUnauthorizedAccount(address)', 'ReentrancyGuardReentrantCall()', 'InvalidInitialization()', 'NotInitializing()','PoolNotInitialized()','OnlyPoolManager()','NotPoolManager()','SenderNotAllowed()','MustUseDynamicFee()','NotDynamicFee()','InvalidFee()','OnlyByPoolManager()','Paused()','EnforcedPause()','NotOwner()','InvalidCaller()','Forbidden()','NotAuthorized()','NotAllowed()','InvalidSender()','PoolNotRegistered()','UnknownPool()','InvalidPoolKey()','InvalidCurrency()','InvalidTickSpacing()','OnlyHook()','NotFactory()','OnlyLaunchpad()','ETHPoolNotAllowed()','UnsupportedInitialize()','OnlyOriginalHook()','PastOrPresentTokenAlreadyLaunched()','InvalidDeployer()','NotLocker()','WethCannotBeClanker()','CannotBeInitializedDirectly()','UnsupportedFee()','CanOnlyBeInitializedByFactory()','OnlyInitializer()','NotPositionManager()','AddLiquidityNotAllowed()','ExactOutNotSupported()','NoDonations()','DonateDisabled()','AddLiquidityThroughHook()','RemoveLiquidityThroughHook()','OnlyAirlock()','OnlyController()','InvalidToken()','TokenNotRegistered()','NotBunniHub()','BunniHook__Unauthorized()','NotHub()']}
def w(x): return (x % (1 << 256)).to_bytes(32, 'big').hex()
def a(x): return x[2:].lower().rjust(64, '0')
def key(c0, c1, fee, ts, hook): return a(c0) + a(c1) + w(fee) + w(ts) + a(hook)
MINP = 4295128740; MAXP = 1461446703485210103287273052203988822378723970341
def cd(name, sender, k, hook_data=''):
    hd = hook_data
    def tail(nhead): return w(nhead * 32) + w(len(hd) // 2) + hd.ljust((len(hd) + 63) // 64 * 64, '0')
    s = SEL[name]
    if name == 'beforeInitialize': return s + a(sender) + k + w(1 << 96)
    if name == 'afterInitialize': return s + a(sender) + k + w(1 << 96) + w(0)
    if name in ('beforeAddLiquidity', 'beforeRemoveLiquidity'):
        ld = 10 ** 15 if 'Add' in name else -10 ** 15
        return s + a(sender) + k + w(-600) + w(600) + w(ld) + w(0) + tail(11)
    if name in ('afterAddLiquidity', 'afterRemoveLiquidity'):
        ld = 10 ** 15 if 'Add' in name else -10 ** 15
        amt = -(10 ** 14) if 'Add' in name else 10 ** 14
        d = ((amt % (1 << 128)) << 128) | (amt % (1 << 128))
        return s + a(sender) + k + w(-600) + w(600) + w(ld) + w(0) + w(d) + w(0) + tail(13)
    if name == 'beforeSwap': return s + a(sender) + k + w(1) + w(-10 ** 18) + w(MINP) + tail(10)
    if name == 'afterSwap':
        d = (((-10 ** 18) % (1 << 128)) << 128) | (9 * 10 ** 17)
        return s + a(sender) + k + w(1) + w(-10 ** 18) + w(MINP) + w(d) + tail(11)
    if name in ('beforeDonate', 'afterDonate'): return s + a(sender) + k + w(10 ** 15) + w(10 ** 15) + tail(9)
def dec_err(data):
    if not data or data == '0x': return 'empty revert'
    d = data[2:]; s = d[:8]; name = ERR.get(s, '0x' + s)
    if name.startswith('WrappedError') and len(d) >= 8 + 64 * 4:
        try:
            tgt = '0x' + d[8 + 24:8 + 64]; sel = d[8 + 64:8 + 72]; o1 = int(d[8 + 128:8 + 192], 16) * 2; l1 = int(d[8 + o1:8 + o1 + 64], 16) * 2
            inner = d[8 + o1 + 64:8 + o1 + 64 + l1]
            fn = [k for k, v in SEL.items() if v == sel]
            return 'Wrapped(%s.%s: %s)' % (tgt[:10], fn[0] if fn else sel, dec_err('0x' + inner))
        except Exception: return name + ' (undecoded)'
    if name == 'Error(string)':
        try:
            l = int(d[8 + 64:8 + 128], 16); return 'Error("%s")' % bytes.fromhex(d[8 + 128:8 + 128 + l * 2]).decode('utf8', 'replace')
        except Exception: pass
    if name == 'Panic(uint256)': return 'Panic(0x%x)' % int(d[8:72], 16)
    return name + ((' ' + d[8:8 + 128]) if len(d) > 8 and name.startswith('0x') else '')
def ecall(u, tx, block='latest'):
    j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [tx, block]})
    if 'error' in j:
        e = j['error']; data = e.get('data')
        if isinstance(data, dict): data = data.get('data') or data.get('result')
        if isinstance(data, str) and data.startswith('0x') and len(data) >= 10: return False, dec_err(data), data
        return False, 'err: ' + str(e.get('message'))[:100] + (' ' + str(data)[:80] if data else ''), None
    return True, j['result'], j['result']
EOA = '0x00000000000000000000000000000000c0ffee01'
FA = '0x1111111111111111111111111111111111111112'; FB = '0x2222222222222222222222222222222222222223'
def probe(cid, hook, urls=None, verbose=True):
    n = net(cid); pm = n['poolManager']; urls = urls or ([n['rpc']] + CFG[cid]['state'])
    u = urls[0]; hook = hook.lower(); out = dict(chainId=cid, hook=hook, flags=flags(hook, False))
    for uu in urls:
        try: code = rpc(uu, 'eth_getCode', [hook, 'latest']); u = uu; break
        except Exception as e: code = None
    out['url'] = u
    cb = bytes.fromhex(code[2:]) if code else b''
    out['codeLen'] = len(cb); out['codeHash'] = keccak256(cb).hex()[:16]
    if len(cb) == 45 and cb[:10].hex() == '363d3d373d3d3d363d73': out['proxy1167'] = '0x' + cb[10:30].hex()
    if len(cb) == 23 and cb[:3].hex() == 'ef0100': out['eip7702'] = '0x' + cb[3:].hex()
    try:
        impl = rpc(u, 'eth_getStorageAt', [hook, '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', 'latest'])
        if int(impl, 16): out['impl1967'] = '0x' + impl[-40:]
    except Exception: pass
    rows = [r for r in load(cid) if r[6] == hook]
    out['pools'] = census(cid)[0].get(hook, 0)
    hl = [r for r in load(cid) if int(r[6], 16) == 0]
    variants = [('fake/fake fee 3000', FA, FB, 3000, 60), ('fake/fake dynamic', FA, FB, 0x800000, 60), ('native/fake fee 3000', '0x' + '0' * 40, FB, 3000, 60), ('native/fake dynamic', '0x' + '0' * 40, FB, 0x800000, 60)]
    if hl:
        r = hl[-1]; variants.append(('foreign real pair %s/%s fee 3000 ts 77' % (r[2][:8], r[3][:8]), r[2], r[3], 3000, 77)); variants.append(('foreign real pair dynamic ts 77', r[2], r[3], 0x800000, 77))
    if rows:
        r = rows[-1]; out['lastPool'] = dict(id=r[1], c0=r[2], c1=r[3], fee=r[4], ts=r[5], block=r[0], tx=r[7])
        ts2 = 77 if r[5] != 77 else 78
        variants.append(('own pair of pool %s, fee %d ts %d' % (r[1][:10], r[4], ts2), r[2], r[3], r[4], ts2))
        import collections
        out['feeModes'] = dict(dynamic=census(cid)[1].get(hook, 0), static=out['pools'] - census(cid)[1].get(hook, 0))
        out['distinctPairs'] = len(set((x[2], x[3]) for x in rows))
    out['init'] = []
    okKeys = []
    for label, c0, c1, fee, ts in variants:
        k = key(c0, c1, fee, ts, hook)
        ok, res, raw = ecall(u, {'from': EOA, 'to': pm, 'data': '0x' + SEL['initialize'] + k + w(1 << 96)})
        out['init'].append(dict(variant=label, ok=ok, result=res if not ok else 'tick ' + str(int(res, 16) if int(res,16) < 2**255 else int(res,16)-2**256)))
        if ok: okKeys.append((label, c0, c1, fee, ts))
    # direct callback calls from the PoolManager with a foreign key (the first accepted variant, else fake/fake)
    tests = okKeys[:1] or [variants[0]]
    if hl and not any(v[0].startswith('foreign real') for v in tests):
        fr = [v for v in okKeys if v[0].startswith('foreign real')]
        tests += fr[:1]
    out['callbacks'] = []
    names = [f for f in out['flags'] if 'ReturnDelta' not in f and 'Initialize' not in f]
    for label, c0, c1, fee, ts in tests:
        k = key(c0, c1, fee, ts, hook)
        for nme in names:
            ok, res, raw = ecall(u, {'from': pm, 'to': hook, 'data': '0x' + cd(nme, EOA, k)})
            if ok:
                r = res[2:]; extra = ''
                if len(r) >= 128: extra = ' ret1=' + r[64:128].lstrip('0')[:40] + (' ret2=' + r[128:192].lstrip('0') if len(r) >= 192 else '')
                res = 'ok sel=' + r[:8] + extra
            out['callbacks'].append(dict(key=label, fn=nme, ok=ok, result=res))
    if verbose:
        print('%d %s pools %d code %d %s %s %s' % (cid, hook, out['pools'], out['codeLen'], out['codeHash'], out.get('proxy1167') or out.get('impl1967') or '', ','.join(flags(hook))))
        print('   feeModes', out.get('feeModes'), 'pairs', out.get('distinctPairs'))
        for i in out['init']: print('   init [%s] -> %s' % (i['variant'], 'OK ' + i['result'] if i['ok'] else i['result']))
        for c in out['callbacks']: print('   cb [%s] %s -> %s' % (c['key'][:24], c['fn'], c['result']))
    os.makedirs('raw/probe', exist_ok=True)
    json.dump(out, open('raw/probe/%d_%s.json' % (cid, hook), 'w'), indent=1)
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1])
    for h in sys.argv[2:]: probe(cid, h)
