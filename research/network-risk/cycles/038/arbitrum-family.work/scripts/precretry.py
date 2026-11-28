"""Cycle 38: resend, one request at a time with a pause, every precscan.py item that came back with a rate limit error, then compare all rows with cycle 20."""
import json, sys, time, urllib.request, ssl
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
NETS = {"42161": ("https://arb1.arbitrum.io/rpc", "0x360e68faccca8ca495c1b759fd9eee466db9fb32"), "4663": ("https://rpc.mainnet.chain.robinhood.com", "0x8366a39cc670b4001a1121b8f6a443a643e40951"), "99901": ("https://rpc.elysium.kinetiq.xyz", "0xe2e105d3f7209a9da11f83ccf3e7398a753823f1")}
P, OLD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
b = json.load(open(P)); a = json.load(open(OLD))
def one(url, m, p):
    for t in range(12):
        body = json.dumps(dict(jsonrpc="2.0", id=1, method=m, params=p)).encode()
        try:
            x = json.load(urllib.request.urlopen(urllib.request.Request(url, body, {"content-type": "application/json", "user-agent": "curl/8"}), timeout=60, context=CTX))
        except Exception as e:
            time.sleep(5 * (t + 1)); continue
        if "error" in x and "Rate Limit" in str(x["error"].get("message")): time.sleep(5 * (t + 1)); continue
        time.sleep(0.4)
        return x.get("result", ("ERR", x.get("error", {}).get("message")))
    return ("ERR", "gave up")
retried = 0
for cid, rows in b.items():
    url, pm = NETS[cid]
    bo = "0x70a08231" + pm[2:].rjust(64, "0"); tr = "0xa9059cbb" + "00" * 12 + "11" * 20 + "%064x" % 1
    for addr, v in rows.items():
        reqs = [("eth_getCode", [addr, "latest"]), ("eth_call", [{"from": pm, "to": addr, "data": "0x"}, "latest"]), ("eth_call", [{"from": pm, "to": addr, "data": bo}, "latest"]), ("eth_call", [{"from": pm, "to": addr, "data": tr}, "latest"])]
        for k in range(4):
            if isinstance(v[k], list) and ("Rate Limit" in str(v[k][1]) or "Too Many" in str(v[k][1])):
                v[k] = one(url, *reqs[k]); retried += 1
diff = []
for cid, rows in b.items():
    for addr, v in rows.items():
        o = a.get(cid, {}).get(addr)
        if json.loads(json.dumps(o)) != json.loads(json.dumps(v)): diff.append({"chainId": cid, "address": addr, "cycle20": o, "cycle38": v})
json.dump({"retried": retried, "rows": sum(len(r) for r in b.values()), "differentFromCycle20": diff, "scan": b}, open(OUT, "w"), indent=0)
print("retried", retried, "rows", sum(len(r) for r in b.values()), "diff", len(diff))
for d in diff: print(json.dumps(d)[:600])
