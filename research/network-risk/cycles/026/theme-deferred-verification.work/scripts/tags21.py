#!/usr/bin/env python3
"""Read-only: for each network in networks.json, read latest, safe, finalized
(number, hash, timestamp), bracketed by web3_clientVersion. Usage: tags21.py NETWORKS.json OUT.json [chainIds...]"""
import json, sys, time, urllib.request

def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": "rpc-probe"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read())
            return j.get("result", {"error": j.get("error")})
    except Exception as e:
        return {"error": repr(e)}

nets = json.load(open(sys.argv[1]))["networks"]
want = set(int(x) for x in sys.argv[3:])
res = []
for n in nets:
    if want and n["chainId"] not in want:
        continue
    url = n["rpc"]
    row = {"chainId": n["chainId"], "name": n["name"], "url": url, "cvStart": rpc(url, "web3_clientVersion", []), "t": time.time()}
    for tag in ["latest", "safe", "finalized"]:
        b = rpc(url, "eth_getBlockByNumber", [tag, False])
        if isinstance(b, dict) and "number" in b:
            row[tag] = {"number": int(b["number"], 16), "hash": b["hash"], "ts": int(b["timestamp"], 16)}
        else:
            row[tag] = b
    row["cvEnd"] = rpc(url, "web3_clientVersion", [])
    try:
        row["safeLagBlocks"] = row["latest"]["number"] - row["safe"]["number"]
        row["safeLagSec"] = row["latest"]["ts"] - row["safe"]["ts"]
    except Exception:
        pass
    try:
        row["finLagBlocks"] = row["latest"]["number"] - row["finalized"]["number"]
        row["finLagSec"] = row["latest"]["ts"] - row["finalized"]["ts"]
    except Exception:
        pass
    res.append(row)
    print(n["chainId"], n["name"], row.get("cvStart"), row.get("safeLagBlocks"), row.get("safeLagSec"), row.get("finLagBlocks"), row.get("finLagSec"), flush=True)
json.dump(res, open(sys.argv[2], "w"), indent=1)
