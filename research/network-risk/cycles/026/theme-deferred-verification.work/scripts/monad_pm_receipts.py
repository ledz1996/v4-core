#!/usr/bin/env python3
"""Read-only: watch PoolManager logs at latest on Monad, record each tx receipt
as first served (blockHash, status), and re-read every receipt after the block
is behind finalized. Usage: monad_pm_receipts.py URL POOLMANAGER SECONDS OUT.json"""
import json, sys, time, urllib.request, urllib.error
URL, PM, SECS, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]

RL = []
def rpc(m, p):
    # Backs off on HTTP 429 (rate limit) and records each one; no attempt to evade the limit.
    for i in range(6):
        req = urllib.request.Request(URL, json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode(),
                                     {"Content-Type": "application/json", "User-Agent": "rpc-probe"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            RL.append([time.time(), m])
            time.sleep(2 * (i + 1))
    raise RuntimeError("rate limited")

out = {"cvStart": rpc("web3_clientVersion", []), "seen": {}, "errors": []}
t0 = time.time(); last = None
while time.time() - t0 < SECS:
    try:
        b = rpc("eth_getBlockByNumber", ["latest", False])["result"]
        n = int(b["number"], 16)
        if n != last:
            last = n
            f = int(rpc("eth_getBlockByNumber", ["finalized", False])["result"]["number"], 16)
            logs = rpc("eth_getLogs", [{"address": PM, "fromBlock": hex(n), "toBlock": hex(n)}]).get("result") or []
            for lg in logs:
                h = lg["transactionHash"]
                if h in out["seen"]:
                    continue
                rc = rpc("eth_getTransactionReceipt", [h]).get("result")
                out["seen"][h] = {"logBlock": n, "logBlockHash": lg["blockHash"], "finalizedAtSeen": f,
                                  "receiptBlockHash": rc and rc["blockHash"], "receiptStatus": rc and rc["status"],
                                  "nLogs": rc and len(rc["logs"]), "t": time.time()}
    except Exception as e:
        out["errors"].append([time.time(), repr(e)])
        time.sleep(1)
    time.sleep(0.2)
time.sleep(15)
out["finalizedAtRecheck"] = int(rpc("eth_getBlockByNumber", ["finalized", False])["result"]["number"], 16)
diff = []
for h, v in out["seen"].items():
    rc = rpc("eth_getTransactionReceipt", [h]).get("result")
    v["finalReceiptBlockHash"] = rc and rc["blockHash"]
    v["finalStatus"] = rc and rc["status"]
    v["finalNLogs"] = rc and len(rc["logs"])
    if (v["finalReceiptBlockHash"], v["finalStatus"], v["finalNLogs"]) != (v["receiptBlockHash"], v["receiptStatus"], v["nLogs"]):
        diff.append(h)
out["changed"] = diff
out["cvEnd"] = rpc("web3_clientVersion", [])
out["rateLimited"] = RL
json.dump(out, open(OUT, "w"), indent=1)
print("txs", len(out["seen"]), "changed", len(diff), "seenBeforeFinal", sum(1 for v in out["seen"].values() if v["logBlock"] > v["finalizedAtSeen"]))
