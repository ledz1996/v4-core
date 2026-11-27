"""Cycle 36 copy of the cycle 34 L-1262 script, run for L-1269 over the blocks with PoolManager logs since 52,371,153. L-1262 on HyperEVM. For every block with PoolManager logs in which two or more transactions touch
the PoolManager, compare the official endpoint's receipts (producer output) with the replica's, and use
the replica's call tracer to find transactions that call the PoolManager without a PoolManager log
(failed or quoted unlocks) that are followed by a later PoolManager transaction in the same block.
Read-only. argv[1] = output json."""
import json, sys, urllib.request, concurrent.futures as cf

PM = "0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f"
OFF = "https://rpc.hyperliquid.xyz/evm"
REP = "https://rpc.purroofgroup.com"
ARCH = "https://rpc.hyperlend.finance/archive"
BASE = "/home/user/v4-core/research/network-risk/cycles/"


def rpc(url, method, params, tries=4):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers={"content-type": "application/json",
                                                                   "user-agent": "network-review-client"})
            with urllib.request.urlopen(req, timeout=120) as r:
                j = json.loads(r.read())
            if "error" in j and i < tries - 1 and "rate" in json.dumps(j["error"]).lower():
                import time; time.sleep(2 + 2 * i); continue
            return j
        except Exception as e:
            err = str(e)
            import time; time.sleep(1 + i)
    return {"error": err}


logs = json.load(open(BASE + "023/theme-hyperevm-twin-state.work/raw/pm_logs_all_hyperlend.json"))["logs"]
try:
    more = json.load(open(BASE + "032/hyperevm.work/out/logs-since-52134673.json"))
    more = more["logs"] if isinstance(more, dict) else more
    logs += [l for l in more if int(l["blockNumber"], 16) > 52266493]
except Exception as e:
    print("no cycle 32 logs", e)
head = int(rpc(ARCH, "eth_blockNumber", [])["result"], 16)
start = 52371153  # cycle 36: same start, targets limited to blocks with logs since start
newlogs = []
b = start
while b <= head:
    e = min(b + 9999, head)
    r = rpc(ARCH, "eth_getLogs", [{"address": PM, "fromBlock": hex(b), "toBlock": hex(e)}])
    if "result" not in r:
        print("getLogs failed", b, e, r); break
    newlogs += r["result"]; b = e + 1
logs += newlogs
print("logs", len(logs), "new since", start, len(newlogs), "head", head)

from collections import defaultdict
blk = defaultdict(set)
for l in logs:
    blk[int(l["blockNumber"], 16)].add(l["transactionHash"].lower())
logtx = {l["transactionHash"].lower() for l in logs}


def walk(frame, hit):
    if (frame.get("to") or "").lower() == PM:
        hit.append({"type": frame.get("type"), "input4": (frame.get("input") or "")[:10],
                    "error": frame.get("error"), "out": (frame.get("output") or "")[:74]})
    for c in frame.get("calls") or []:
        walk(c, hit)


def norm_receipt(r):
    return {"tx": r["transactionHash"].lower(), "status": r.get("status"), "gasUsed": r.get("gasUsed"),
            "cum": r.get("cumulativeGasUsed"),
            "logs": [(l["address"].lower(), tuple(l["topics"]), l["data"]) for l in r.get("logs", [])]}


def do_block(n):
    res = {"block": n}
    ro = rpc(OFF, "eth_getBlockReceipts", [hex(n)])
    rr = rpc(ARCH, "eth_getBlockReceipts", [hex(n)])
    ho = rpc(OFF, "eth_getBlockByNumber", [hex(n), False]).get("result") or {}
    hr = rpc(ARCH, "eth_getBlockByNumber", [hex(n), False]).get("result") or {}
    res["receiptsRootEqual"] = ho.get("receiptsRoot") == hr.get("receiptsRoot") and ho.get("receiptsRoot") is not None
    res["hashEqual"] = ho.get("hash") == hr.get("hash") and ho.get("hash") is not None
    if "result" in ro and "result" in rr and ro["result"] is not None and rr["result"] is not None:
        a = [norm_receipt(x) for x in ro["result"]]
        c = [norm_receipt(x) for x in rr["result"]]
        res["receiptsEqual"] = a == c
        res["nReceipts"] = len(a)
    else:
        res["receiptsEqual"] = None
        res["err"] = [str(ro.get("error"))[:200], str(rr.get("error"))[:200]]
        a = []
    tr = rpc(REP, "debug_traceBlockByNumber", [hex(n), {"tracer": "callTracer"}])
    pmtx = []
    if "result" in tr and tr["result"]:
        for i, t in enumerate(tr["result"]):
            res_t = t.get("result") or {}
            hit = []
            walk(res_t, hit)
            if hit:
                h = (t.get("txHash") or "").lower()
                if not h and i < len(a):
                    h = a[i]["tx"]
                pmtx.append({"idx": i, "tx": h, "hasPmLog": h in logtx, "frames": hit,
                             "topError": res_t.get("error")})
        res["traced"] = True
    else:
        res["traced"] = False
        res["traceErr"] = str(tr.get("error"))[:200]
    res["pmtx"] = pmtx
    # pattern: a PM-touching tx without PM log (or with failed PM frame) followed by a later PM tx with logs
    pat = []
    for j, p in enumerate(pmtx):
        failed = (not p["hasPmLog"]) or any(f["error"] for f in p["frames"])
        if failed:
            later = [q for q in pmtx[j + 1:] if q["hasPmLog"]]
            if later:
                pat.append({"failedTx": p["tx"], "laterTx": [q["tx"] for q in later]})
    res["pattern"] = pat
    return res


targets = sorted(b for b, t in blk.items() if len(t) >= 2)
# also every block with PM logs since start (new activity)
targets = sorted({int(l["blockNumber"], 16) for l in newlogs})
print("target blocks", len(targets))
out = []
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(do_block, targets):
        out.append(r)
summary = {
    "blocks": len(out),
    "receiptsEqual": sum(1 for r in out if r.get("receiptsEqual")),
    "receiptsUnknown": sum(1 for r in out if r.get("receiptsEqual") is None),
    "receiptsRootEqual": sum(1 for r in out if r["receiptsRootEqual"]),
    "hashEqual": sum(1 for r in out if r["hashEqual"]),
    "traced": sum(1 for r in out if r["traced"]),
    "blocksWithPattern": sum(1 for r in out if r["pattern"]),
    "patternPairs": sum(len(r["pattern"]) for r in out),
    "newLogs": len(newlogs), "head": head,
}
print(json.dumps(summary))
json.dump({"summary": summary, "newlogs": newlogs, "blocks": out}, open(sys.argv[1], "w"), indent=1)
