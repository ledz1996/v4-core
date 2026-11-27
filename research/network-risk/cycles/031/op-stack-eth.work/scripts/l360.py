# Read-only probe for lead L-360: eth_call with state overrides on Base; no transaction is sent.
import json, sys, urllib.request
URL = sys.argv[1] if len(sys.argv) > 1 else "https://mainnet.base.org"
PM = "0x498581ff718922c3f8e6a244956af099b2652b2b"
TOK = "0xB2000000000000000000002fEb517dFeC7415344"
FAC = "0xB20f000000000000000000000000000000000000"
REG = "0x8453000000000000000000000000000000000002"
HELP = "0x00000000000000000000000000000000c0ffee01"
RCPT = "000000000000000000000000000000000000000000000000000000000000beef"
def rpc(m, p):
    r = urllib.request.Request(URL, json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), {"content-type":"application/json","user-agent":"probe"})
    return json.load(urllib.request.urlopen(r, timeout=30))
def helper(target, op):
    a = target[2:].lower()
    pre = "365f5f37"
    if op == "dc":   call = "5f5f365f" + "73" + a + "5af4"
    elif op == "cc": call = "5f5f365f5f" + "73" + a + "5af2"
    else:            call = "5f5f365f5f" + "73" + a + "5af1"
    post = "5f523d5f60203e3d6020015ff3"
    return "0x" + pre + call + post
blk = rpc("eth_blockNumber", [])["result"]
out = {"url": URL, "block": int(blk, 16), "client": rpc("web3_clientVersion", [])["result"]}
bal = "0x70a08231" + "0"*24 + PM[2:]
out["balanceOfPM"] = rpc("eth_call", [{"to": TOK, "data": bal}, blk])
xfer = "0xa9059cbb" + RCPT + "%064x" % 1
for name, tgt, data in [("token", TOK, xfer), ("factory", FAC, "0x00000000"), ("registry", REG, "0x00000000")]:
    for op in ["dc", "cc", "call"]:
        res = rpc("eth_call", [{"from": PM, "to": HELP, "data": data, "gas": "0x1c9c380"}, blk, {HELP: {"code": helper(tgt, op)}}])
        out[f"{name}-{op}"] = res
print(json.dumps(out, indent=1))
