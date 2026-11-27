# Read-only: does eth_call with a block time override past lagoon_time apply Lagoon rules?
# Observable: BLS12-381 G1 MSM (0x0c) input of 818 zero pairs (130,880 bytes) is allowed before Lagoon (limit 1,806 pairs) and refused after (limit 817).
import json, sys, urllib.request
LAGOON = 1799683201
def rpc(url, m, p):
    r = urllib.request.Request(url, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), {"content-type":"application/json","user-agent":"probe"})
    try: return json.load(urllib.request.urlopen(r, timeout=60))
    except Exception as e: return {"exc": str(e)[:200]}
out = {}
for url in sys.argv[1:]:
    res = {"client": rpc(url, "web3_clientVersion", [])}
    for pairs in (817, 818):
        data = "0x" + "00" * (160 * pairs)
        call = {"to": "0x000000000000000000000000000000000000000c", "data": data, "gas": hex(25_000_000)}
        for label, extra in (("now", []), ("lagoon", [{}, {"time": hex(LAGOON + 100)}]), ("lagoon-1", [{}, {"time": hex(LAGOON - 100)}])):
            r = rpc(url, "eth_call", [call, "latest"] + extra)
            if "result" in r: r = {"resultLen": (len(r["result"]) - 2) // 2, "head": r["result"][:20]}
            res[f"{pairs}-{label}"] = r
    out[url] = res
print(json.dumps(out, indent=1))
