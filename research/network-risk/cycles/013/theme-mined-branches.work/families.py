"""Branch families of the plan, decoded from a callTracer (withLog) tree and the rerun's base state."""
import sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
import v4math as V
def sel(s): return '0x' + keccak(s.encode())[:4].hex()
K = '(address,address,uint24,int24,address)'
PMSEL = {sel(x): x.split('(')[0] for x in ['unlock(bytes)', f'swap({K},(bool,int256,uint160),bytes)', f'modifyLiquidity({K},(int24,int24,int256,bytes32),bytes)',
    'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'sync(address)', 'mint(address,uint256,uint256)', 'burn(address,uint256,uint256)',
    f'donate({K},uint256,uint256,bytes)', f'initialize({K},uint160)', 'clear(address,uint256)', 'transfer(address,uint256,uint256)',
    'transferFrom(address,address,uint256,uint256)', 'approve(address,uint256,uint256)', 'setOperator(address,bool)',
    f'updateDynamicLPFee({K},uint24)', 'extsload(bytes32)', 'exttload(bytes32)', 'extsload(bytes32[])', 'exttload(bytes32[])', 'extsload(bytes32,uint256)',
    'collectProtocolFees(address,address,uint256)', 'balanceOf(address,uint256)', 'allowance(address,address,uint256)', 'isOperator(address,address)']}
HOOKSEL = {'0xdc98354e': 'beforeInitialize', '0x6fe7e6eb': 'afterInitialize', '0x259982e5': 'beforeAddLiquidity', '0x9f063efc': 'afterAddLiquidity',
           '0x21d0ee70': 'beforeRemoveLiquidity', '0x6c2bbe7e': 'afterRemoveLiquidity', '0x575e24b4': 'beforeSwap', '0xb47b2fb1': 'afterSwap',
           '0xb6a8b0fa': 'beforeDonate', '0xe1b4af69': 'afterDonate'}
SWAPLOG = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
MAX = (1 << 256) - 1
def w(hexs, i): return int(hexs[10 + 64 * i:10 + 64 * (i + 1)] or '0', 16)
def s256(x): return x - (1 << 256) if x >> 255 else x
def s24(x): x &= 0xffffff; return x - (1 << 24) if x >> 23 else x

def families(ct, pm, sload=None):
    """Returns a dict family -> count for the PoolManager frames in this transaction that completed
    (inside a frame that did not revert) plus the same with suffix ':undone' for reverted ones."""
    fam = {}
    def add(k, undone):
        k = k + (':undone' if undone else ''); fam[k] = fam.get(k, 0) + 1
    def walk(n, rev, parent_from_pm, parent_hooksel):
        err = 'error' in n; rev2 = rev or err
        to = (n.get('to') or '').lower(); inp = (n.get('input') or '0x').lower(); frm = (n.get('from') or '').lower()
        if to == pm and n.get('type') == 'CALL':
            s = PMSEL.get(inp[:10], inp[:10])
            if parent_from_pm and parent_hooksel: add('pmCallFromInsideHookCallback:' + parent_hooksel, rev2)
            if not err:
                if s == 'clear': add('clearExact', rev2)
                if s == 'settleFor': add('settleFor', rev2 if True else rev2); 
                if s == 'settleFor' and int(n.get('value', '0x0') or '0x0', 16): add('settleForNative', rev2)
                if s in ('mint', 'burn', 'donate', 'setOperator', 'approve', 'transfer', 'updateDynamicLPFee', 'collectProtocolFees', 'initialize'): add(s, rev2)
                if s == 'take' and w(inp, 0) == 0: add('takeNative', rev2)
                if s in ('transferFrom', 'burn') and sload:
                    owner = w(inp, 0); spender = int(frm, 16); idv = w(inp, 2) if s == 'transferFrom' else w(inp, 1)
                    if owner == spender: add(s + ':self', rev2)
                    else:
                        op = sload(int.from_bytes(keccak(spender.to_bytes(32, 'big') + keccak(owner.to_bytes(32, 'big') + (3).to_bytes(32, 'big'))), 'big'))
                        if op: add(s + ':operator', rev2)
                        else:
                            a = sload(int.from_bytes(keccak(idv.to_bytes(32, 'big') + keccak(spender.to_bytes(32, 'big') + keccak(owner.to_bytes(32, 'big') + (5).to_bytes(32, 'big')))), 'big'))
                            add(s + (':infiniteAllowance' if a == MAX else ':finiteAllowance'), rev2)
                if s in ('swap', 'modifyLiquidity', 'donate'):
                    hooks = w(inp, 4); fee = w(inp, 2); spacing = s24(w(inp, 3))
                    if hooks:
                        add(s + ':hooked', rev2)
                        for bit, name in ((3, 'beforeSwapReturnDelta'), (2, 'afterSwapReturnDelta'), (1, 'afterAddLiquidityReturnDelta'), (0, 'afterRemoveLiquidityReturnDelta')):
                            if hooks >> bit & 1 and ((s == 'swap' and bit >= 2) or (s == 'modifyLiquidity' and bit < 2)):
                                if s == 'modifyLiquidity':
                                    ld = s256(w(inp, 7))
                                    if (bit == 1 and ld <= 0) or (bit == 0 and ld > 0): continue
                                add('hookFlag:' + name, rev2)
                    if fee == 0x800000 and s == 'swap': add('swap:dynamicFeePool', rev2)
                if s == 'swap':
                    zf = w(inp, 5); amt = s256(w(inp, 6)); lim = w(inp, 7)
                    if amt > 0: add('swap:exactOutput', rev2)
                    for c in n.get('calls', []) or []:
                        if (c.get('input') or '')[:10] == '0x575e24b4' and 'error' not in c and fee == 0x800000:
                            o = (c.get('output') or '0x')[2:]
                            if len(o) >= 192 and int(o[128:192], 16) & 0x400000: add('swap:lpFeeOverride', rev2)
                        if (c.get('input') or '')[:10] in ('0x575e24b4', '0xb47b2fb1') and 'error' not in c:
                            o = (c.get('output') or '0x')[2:]
                            if len(o) >= 128 and int(o[64:128], 16) and ((c['input'][:10] == '0x575e24b4' and hooks >> 3 & 1) or (c['input'][:10] == '0xb47b2fb1' and hooks >> 2 & 1)):
                                add('hookReturnedNonzeroDelta:' + HOOKSEL[c['input'][:10]], rev2)
                    for lg in n.get('logs', []) or []:
                        if lg['address'].lower() == pm and lg['topics'][0].lower() == SWAPLOG:
                            d = lg['data'][2:]; price = int(d[128:192], 16); tick = s256(int(d[256:320], 16))
                            if price == lim: add('swap:endsAtPriceLimit', rev2)
                            for t in (tick, tick + 1):
                                if -887272 <= t <= 887272 and V.get_sqrt_price_at_tick(t) == price and t % spacing == 0:
                                    init = None
                                    if sload:
                                        pid = keccak(bytes.fromhex(inp[10:10 + 64 * 5]))
                                        base = int.from_bytes(keccak(pid + (6).to_bytes(32, 'big')), 'big') + 4
                                        init = sload(int.from_bytes(keccak((t % (1 << 256)).to_bytes(32, 'big') + base.to_bytes(32, 'big')), 'big')) & ((1 << 128) - 1)
                                    add('swap:endsOnInitializedTick' if init else 'swap:endsOnTickBoundary', rev2)
        hs = HOOKSEL.get(inp[:10]) if frm == pm else None
        for c in n.get('calls', []) or []:
            walk(c, rev2, frm == pm, hs)
    walk(ct, False, False, None)
    return fam
