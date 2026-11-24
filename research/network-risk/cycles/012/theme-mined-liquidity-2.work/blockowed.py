"""For blocks where a native leg could not be attributed (no tracer, other PoolManager transactions in the block):
run analyze3's per-transaction rerun for every transaction of the block that emitted a PoolManager log, add up the
native amount the source says the PoolManager owed in each, and compare the total with the PoolManager's balance
difference that block production wrote. A transaction whose events analyze3 cannot model leaves the block open.
Usage: blockowed.py <chainId> <blocks.json> <out.json>"""
import sys, json
cid, blocks_f, out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = ['analyze3.py', cid, '/dev/null', '0', '1']
import analyze3 as A
res = []
for b in json.load(open(blocks_f)):
    logs = A.block_pm_logs(b); txs = []
    for l in sorted(logs, key=lambda x: int(x['logIndex'], 16)):
        if l['transactionHash'] not in txs: txs.append(l['transactionHash'])
    tot = 0; open_ = []; per = {}
    for h in txs:
        try: r = A.one(h, b)
        except Exception as e: open_.append([h, repr(e)[:120]]); continue  # noqa
        if 'aside' in r: open_.append([h, r['aside']]); continue
        ow = int(r.get('currencies', {}).get('0x' + '0' * 40, {}).get('owed', '0')); per[h] = str(ow); tot += ow
        if r['storageMismatch']: open_.append([h, 'storage ' + ','.join(r['storageMismatch'][:3])])
    bd = int(A.rpc(A.cid, 'eth_getBalance', [A.PM, hex(b)], urls=A.SU), 16) - int(A.rpc(A.cid, 'eth_getBalance', [A.PM, hex(b - 1)], urls=A.SU), 16)
    rec = {'block': b, 'pmTxs': len(txs), 'nativeOwedPerTx': per, 'totalOwed': str(tot), 'balanceDiff': str(bd), 'open': open_,
           'reconciled': (not open_) and bd == -tot}
    res.append(rec); print(json.dumps(rec)[:600], flush=True)
json.dump(res, open(out, 'w'), indent=1)
