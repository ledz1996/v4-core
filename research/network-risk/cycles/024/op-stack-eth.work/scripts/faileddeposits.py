"""Read-only census for lead L-985: every block with a PoolManager log on one chain,
then the block's receipts; report deposits (type 0x7e) with status 0 that precede a
PoolManager transaction in the same block. Usage: faileddeposits.py <rpc> <pm> <from> <to> <step> <out.json>"""
import sys, json, urllib.request, time
rpc, pm, lo, hi, step, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
def call(m, p, tries=5):
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(rpc, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), {"content-type":"application/json","user-agent":"census"}), timeout=60)
            j = json.load(r)
            if 'error' in j: raise RuntimeError(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + i)
    raise err
blocks = {}
b = lo
while b <= hi:
    e = min(hi, b + step - 1)
    try:
        logs = call("eth_getLogs", [{"address": pm, "fromBlock": hex(b), "toBlock": hex(e)}])
    except Exception as ex:
        if step > 1000:
            step //= 4; continue
        raise
    for l in logs:
        blocks.setdefault(int(l['blockNumber'], 16), set()).add(l['transactionHash'])
    b = e + 1
res = {"rpc": rpc, "pm": pm, "range": [lo, hi], "blocksWithPMLogs": len(blocks), "pmTxs": sum(len(v) for v in blocks.values()), "depositsTotal": 0, "failedDeposits": [], "failedDepositBeforePM": []}
for n in sorted(blocks):
    rc = call("eth_getBlockReceipts", [hex(n)])
    for r in rc:
        if r.get('type') == '0x7e':
            res['depositsTotal'] += 1
            if r.get('status') == '0x0':
                res['failedDeposits'].append({"block": n, "tx": r['transactionHash'], "index": int(r['transactionIndex'], 16)})
                pmidx = [int(x['transactionIndex'], 16) for x in rc if x['transactionHash'] in blocks[n]]
                if any(i > int(r['transactionIndex'], 16) for i in pmidx):
                    res['failedDepositBeforePM'].append({"block": n, "deposit": r['transactionHash'], "pmTxIndexes": pmidx})
json.dump(res, open(out, 'w'), indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})
