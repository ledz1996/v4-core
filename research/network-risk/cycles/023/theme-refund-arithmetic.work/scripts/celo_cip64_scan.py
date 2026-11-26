# Read-only scan of recent Celo blocks for CIP-64 (type 0x7b) transactions whose
# main call transfers the fee currency back to the sender (the F-144 shape candidate).
import json, sys, urllib.request, time
R = "https://forno.celo.org"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def rpc(m, p):
    req = urllib.request.Request(R, data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),
                                 headers={"content-type":"application/json","user-agent":"rpc-reader"})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            time.sleep(1+i)
    return {"error": "fail"}
n = int(sys.argv[1]); out = sys.argv[2]
cv = rpc("web3_clientVersion", [])
head = int(rpc("eth_blockNumber", [])["result"], 16)
res = {"clientVersionStart": cv.get("result"), "head": head, "blocks": n, "cip64": 0, "candidates": []}
for b in range(head - n + 1, head + 1):
    blk = rpc("eth_getBlockByNumber", [hex(b), True]).get("result")
    if not blk: continue
    txs = [t for t in blk["transactions"] if t.get("type") == "0x7b"]
    if not txs: continue
    rc = rpc("eth_getBlockReceipts", [hex(b)]).get("result") or []
    rmap = {r["transactionHash"]: r for r in rc}
    for t in txs:
        res["cip64"] += 1
        fc = (t.get("feeCurrency") or "").lower()
        r = rmap.get(t["hash"]);
        if not r: continue
        snd = t["from"].lower()[2:]
        logs = r["logs"]
        tr = [l for l in logs if l["topics"] and l["topics"][0] == TRANSFER and len(l["topics"]) == 3]
        if not tr: continue
        d = tr[0]  # the CIP-64 debit is recorded first (logs_pre)
        if d["topics"][1][-40:] != snd: continue
        tok = d["address"].lower(); holder = d["topics"][2][-40:]
        ins = [l for l in tr[1:] if l["address"].lower() == tok and l["topics"][2][-40:] == snd
               and l["topics"][1][-40:] not in (holder, "0"*40)]
        if ins:
            res["candidates"].append({"block": b, "hash": t["hash"], "feeCurrency": fc, "token": tok, "from": t["from"],
                "gas": int(t["gas"], 16), "gasUsed": int(r["gasUsed"], 16), "inTransfers": len(ins)})
res["clientVersionEnd"] = rpc("web3_clientVersion", []).get("result")
json.dump(res, open(out, "w"), indent=1)
print(res["cip64"], len(res["candidates"]))
