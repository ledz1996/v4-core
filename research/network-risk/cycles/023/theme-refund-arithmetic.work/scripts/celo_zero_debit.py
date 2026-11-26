# For a seeded sample of scan candidates, test read-only whether the CIP-64 debit took the
# sender's fee-token balance to zero (pre-tx balance at block-1 equals the debit amount, and
# the sender has no earlier transaction in the same block).
import json, sys, random, urllib.request, time
R = "https://forno.celo.org"
def rpc(m, p):
    req = urllib.request.Request(R, data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),
                                 headers={"content-type":"application/json","user-agent":"rpc-reader"})
    for i in range(4):
        try: return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception: time.sleep(1+i)
    return {}
scan = json.load(open(sys.argv[1])); seed = int(sys.argv[2]); k = int(sys.argv[3])
random.seed(seed); sample = random.sample(scan["candidates"], min(k, len(scan["candidates"])))
out = {"seed": seed, "k": len(sample), "clientVersionStart": rpc("web3_clientVersion", []).get("result"), "rows": []}
for c in sample:
    rc = rpc("eth_getTransactionReceipt", [c["hash"]]).get("result")
    d = [l for l in rc["logs"] if l["topics"][0].startswith("0xddf252ad")][0]
    debit = int(d["data"], 16)
    blk = rpc("eth_getBlockByNumber", [hex(c["block"]), False])["result"]
    idx = blk["transactions"].index(c["hash"])
    earlier = False
    for h in blk["transactions"][:idx]:
        tx = rpc("eth_getTransactionByHash", [h]).get("result") or {}
        if tx.get("from","").lower() == c["from"].lower(): earlier = True; break
    data = "0x70a08231" + c["from"][2:].lower().rjust(64, "0")
    bal = int(rpc("eth_call", [{"to": c["token"], "data": data}, hex(c["block"]-1)])["result"], 16)
    out["rows"].append({**c, "debit": debit, "preBalanceBlockMinus1": bal, "earlierTxSameSender": earlier,
                        "debitClearsSlot": (not earlier) and bal == debit})
out["clientVersionEnd"] = rpc("web3_clientVersion", []).get("result")
out["clearing"] = sum(r["debitClearsSlot"] for r in out["rows"])
json.dump(out, open(sys.argv[4], "w"), indent=1)
print(out["k"], out["clearing"])
