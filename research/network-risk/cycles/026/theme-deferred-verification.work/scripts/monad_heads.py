#!/usr/bin/env python3
"""Read-only sampler: records blocks served at latest on a Monad endpoint, then
re-reads the same numbers after they are behind finalized and compares hashes.
No seed needed (no random sampling: every distinct head seen is recorded).
Usage: monad_heads.py URL N OUT.json"""
import json, sys, time, urllib.request

URL, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]

def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "User-Agent": "rpc-probe"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

out = {"url": URL, "clientVersionStart": rpc("web3_clientVersion", []), "heads": {}, "tagSnapshots": [], "errors": []}
t0 = time.time()
i = 0
while len(out["heads"]) < N and time.time() - t0 < 3600:
    try:
        b = rpc("eth_getBlockByNumber", ["latest", False])["result"]
        n = int(b["number"], 16)
        if str(n) not in out["heads"]:
            out["heads"][str(n)] = {"hash": b["hash"], "parent": b["parentHash"], "seenAt": time.time()}
        if i % 50 == 0:
            snap = {"t": time.time()}
            for tag in ["latest", "safe", "finalized"]:
                r = rpc("eth_getBlockByNumber", [tag, False]).get("result") or {}
                snap[tag] = [r.get("number"), r.get("hash"), r.get("timestamp")]
            out["tagSnapshots"].append(snap)
    except Exception as e:
        out["errors"].append([time.time(), repr(e)])
        time.sleep(1)
    i += 1
    time.sleep(0.15)
out["clientVersionMid"] = rpc("web3_clientVersion", [])
# wait until the highest head is behind finalized
top = max(int(k) for k in out["heads"])
for _ in range(120):
    f = int(rpc("eth_getBlockByNumber", ["finalized", False])["result"]["number"], 16)
    if f >= top:
        break
    time.sleep(2)
out["finalizedAtRecheck"] = f
mism = []
for k, v in sorted(out["heads"].items(), key=lambda kv: int(kv[0])):
    for attempt in range(3):
        try:
            b = rpc("eth_getBlockByNumber", [hex(int(k)), False])["result"]
            break
        except Exception as e:
            b = None
            time.sleep(1)
    v["finalHash"] = b["hash"] if b else None
    if v["finalHash"] != v["hash"]:
        mism.append({"number": int(k), **v})
out["mismatches"] = mism
# parent links among consecutive heads seen
gaps = 0; brk = []
ks = sorted(int(k) for k in out["heads"])
for a, b2 in zip(ks, ks[1:]):
    if b2 == a + 1:
        if out["heads"][str(b2)]["parent"] != out["heads"][str(a)]["hash"]:
            brk.append(a)
    else:
        gaps += 1
out["parentLinkBreaks"] = brk
out["numberGaps"] = gaps
out["clientVersionEnd"] = rpc("web3_clientVersion", [])
json.dump(out, open(OUT, "w"), indent=1)
print("heads", len(out["heads"]), "mismatches", len(mism), "breaks", len(brk), "gaps", gaps)
