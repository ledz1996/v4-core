"""Summarise PoolManager-only replays. Usage: report.py <out.json> <chainId>:<pm-jsonl> ..."""
import sys, json, collections
new83 = json.load(open('new83.json')); N = {(x['pc'], x['newSide']): x for x in new83}
FAM = ['clearExact', 'transferFrom:finiteAllowance', 'transferFrom:infiniteAllowance', 'transferFrom:operator', 'transferFrom:self',
       'burn:finiteAllowance', 'burn:infiniteAllowance', 'burn:operator', 'burn:self', 'setOperator', 'approve', 'transfer',
       'hookFlag:beforeSwapReturnDelta', 'hookFlag:afterSwapReturnDelta', 'hookFlag:afterAddLiquidityReturnDelta', 'hookFlag:afterRemoveLiquidityReturnDelta',
       'hookReturnedNonzeroDelta:beforeSwap', 'hookReturnedNonzeroDelta:afterSwap', 'pmCallFromInsideHookCallback:*', 'swap:dynamicFeePool', 'swap:lpFeeOverride',
       'donate', 'settleFor', 'settleForNative', 'mint', 'burn', 'takeNative', 'swap:endsAtPriceLimit', 'swap:exactOutput', 'swap:endsOnInitializedTick',
       'swap:endsOnTickBoundary', 'updateDynamicLPFee', 'initialize', 'collectProtocolFees']
def ok(r):
    return (not r.get('divergence') and r['frames'][1] and r['logs'][2] and r.get('storageVsDiff', [0, 0, True])[2]
            and r.get('storageVsBlock', [0, True])[1])
out = {}
if __name__ != "__main__": sys.argv = sys.argv[:1]
for arg in sys.argv[2:]:
    cid, f = arg.split(':', 1); rs = [json.loads(l) for l in open(f)]
    c = collections.Counter(); fam = {k: collections.Counter() for k in FAM}; br = collections.Counter(); brm = collections.Counter()
    bad = []
    for r in rs:
        if 'error' in r: c['rpcError'] += 1; continue
        if 'setAside' in r: c['setAside'] += 1; continue
        if 'divergence' in r and 'frames' not in r: c['divergence'] += 1; bad.append(r); continue
        c['replayed'] += 1; m = ok(r); c['matched' if m else 'unmatched'] += 1
        if not m: bad.append(r)
        c['storageBlockChecked'] += 'storageVsBlock' in r
        fs = r.get('families', {})
        for k in FAM:
            n = sum(v for kk, v in fs.items() if (kk == k or (k.endswith('*') and kk.startswith(k[:-1]))) and not kk.endswith(':undone'))
            nu = sum(v for kk, v in fs.items() if (kk == k + ':undone' or (k.endswith('*') and kk.startswith(k[:-1]) and kk.endswith(':undone'))))
            if n or nu:
                fam[k]['tx'] += 1; fam[k]['frames'] += n; fam[k]['undoneFrames'] += nu
                fam[k]['matched' if m else 'unmatched'] += 1
        for pc, o in r.get('branches', []):
            if (pc, o) in N: br[(pc, o)] += 1; brm[(pc, o)] += m
    out[cid] = {'counts': dict(c), 'families': {k: dict(v) for k, v in fam.items()},
                'new83': [{'pc': x['pc'], 'side': x['newSide'], 'src': f"{x['file']}:{x['line']}", 'snippet': x['snippet'][:70], 'txs': br[(x['pc'], x['newSide'])], 'matched': brm[(x['pc'], x['newSide'])]} for x in new83],
                'unmatched': [{k: r.get(k) for k in ('tx', 'block', 'status', 'divergence', 'frames', 'frameMismatch', 'logs', 'storageVsDiff', 'storageDiffDetail', 'storageVsBlock', 'storageBlockDetail', 'families')} for r in bad[:40]]}
    print(cid, dict(c)); print('  families', {k: dict(v) for k, v in fam.items() if v})
    print('  new83 with mined instance', sum(1 for k in N if br[k]), [(k, br[k]) for k in N if br[k]])
if len(sys.argv) > 1: json.dump(out, open(sys.argv[1], "w"), indent=1)
