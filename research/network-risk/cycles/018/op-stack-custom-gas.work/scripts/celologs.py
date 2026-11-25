"""Scan Celo PoolManager ModifyLiquidity logs from deployment (block 43,985,163) to head. Read-only.
Usage: python3 celologs.py <out.json> <url> <step> [from] [to]"""
import sys, json, urllib.request, concurrent.futures as cf, time
PM = "0x288dc841A52FCA2707c6947B3A777c5E56cd87BC"
MOD = "0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec"
out, url, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
lo = int(sys.argv[4]) if len(sys.argv) > 4 else 43985163
def rpc(m, p):
    for k in range(10):
        try:
            r = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            j = json.load(urllib.request.urlopen(r, timeout=90))
            if 'error' in j: raise RuntimeError(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + k)
    raise err
hi = int(sys.argv[5]) if len(sys.argv) > 5 else int(rpc("eth_blockNumber", []), 16)
ranges = [(a, min(a + step - 1, hi)) for a in range(lo, hi + 1, step)]
def get(r):
    return rpc("eth_getLogs", [{"address": PM, "topics": [MOD], "fromBlock": hex(r[0]), "toBlock": hex(r[1])}])
logs = []; fails = []
with cf.ThreadPoolExecutor(6) as ex:
    futs = {ex.submit(get, r): r for r in ranges}
    for f in cf.as_completed(futs):
        try: logs += f.result()
        except Exception as e: fails.append([futs[f], str(e)[:200]])
logs.sort(key=lambda l: (int(l['blockNumber'], 16), int(l['logIndex'], 16)))
json.dump({"url": url, "from": lo, "to": hi, "step": step, "ranges": len(ranges), "fails": fails, "logs": logs}, open(out, "w"))
print("ranges", len(ranges), "logs", len(logs), "fails", len(fails))
