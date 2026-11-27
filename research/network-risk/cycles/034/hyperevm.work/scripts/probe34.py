"""Cycle 34 HyperEVM probes: deployment parity (L5), fork probe, HyperCore info reads.
Read-only: eth_call, eth_getCode, eth_getStorageAt, info endpoint POSTs. Writes JSON to argv[1]."""
import json, sys, hashlib, urllib.request

PM = "0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F"
EPS = ["https://rpc.hyperliquid.xyz/evm", "https://rpc.purroofgroup.com",
       "https://rpc.hyperlend.finance/archive"]
TESTNET = "https://rpc.hyperliquid-testnet.xyz/evm"
INFO = "https://api.hyperliquid.xyz/info"


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json",
                                          "user-agent": "network-review-client"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except Exception as e:  # keep the error text
        return {"error": str(e)}


def rpc(url, method, params):
    return post(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})


def call(url, to, data, code=None, gas="0x1c9c380"):
    tx = {"to": to, "data": data, "gas": gas}
    ov = {to: {"code": code}} if code else None
    p = [tx, "latest"] + ([ov] if ov else [])
    return rpc(url, "eth_call", p)


out = {}
# L5 parity
for ep in EPS:
    r = {}
    r["clientVersion"] = rpc(ep, "web3_clientVersion", [])
    r["block"] = rpc(ep, "eth_blockNumber", [])
    code = rpc(ep, "eth_getCode", [PM, "latest"]).get("result", "")
    b = bytes.fromhex(code[2:]) if code else b""
    r["codeLen"] = len(b)
    r["codeSha256"] = hashlib.sha256(b).hexdigest()
    r["owner"] = call(ep, PM, "0x8da5cb5b")
    r["protocolFeeController"] = call(ep, PM, "0xf02de3b2")
    r["slot0"] = rpc(ep, "eth_getStorageAt", [PM, "0x0", "latest"])
    r["slot1"] = rpc(ep, "eth_getStorageAt", [PM, "0x1", "latest"])
    r["nonce"] = rpc(ep, "eth_getTransactionCount", [PM, "latest"])
    r["balance"] = rpc(ep, "eth_getBalance", [PM, "latest"])
    own = r["owner"].get("result", "0x")
    if len(own) >= 66:
        oa = "0x" + own[-40:]
        oc = rpc(ep, "eth_getCode", [oa, "latest"]).get("result", "")
        r["ownerCodeLen"] = (len(oc) - 2) // 2 if oc else None
        r["ownerCodeSha256"] = hashlib.sha256(bytes.fromhex(oc[2:])).hexdigest() if oc else None
    out[ep] = r

# fork probe: opcodes of Osaka/Prague and newer that the PoolManager could meet
A = "0x00000000000000000000000000000000000c0de5"
probes = {
    "CLZ(1)": "0x6001" + "1e" + "5f5260205ff3",
    "TLOAD/TSTORE": "0x602a5f5d5f5c5f5260205ff3",
    "MCOPY": "0x60205f5f5e5f5160005260205ff3",
    "PUSH0": "0x5f5f5260205ff3",
    "BLOBBASEFEE": "0x4a5f5260205ff3",
    "SELFBALANCE": "0x475f5260205ff3",
    "DUPN(0xe6)": "0x6001e6005f5260205ff3",
    "SWAPN(0xe7)": "0x60016002e7005f5260205ff3",
    "EXCHANGE(0xe8)": "0x600160026003e8005f5260205ff3",
}
fp = {}
for ep in [EPS[0], TESTNET]:
    r = {"clientVersion": rpc(ep, "web3_clientVersion", []), "block": rpc(ep, "eth_blockNumber", [])}
    for k, code in probes.items():
        r[k] = call(ep, A, "0x", code)
    for name, addr in [("p256verify 0x100", "0x0000000000000000000000000000000000000100"),
                       ("bls12 g1add 0x0b", "0x000000000000000000000000000000000000000b"),
                       ("history 0x0000F908", "0x0000F90827F1C53a10cb7A02335B175320002935"),
                       ("beaconroots", "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02")]:
        r[name] = {"code": rpc(ep, "eth_getCode", [addr, "latest"]).get("result"),
                   "call160": call(ep, addr, "0x" + "00" * 160)}
    r["eth_config"] = rpc(ep, "eth_config", [])
    r["type4"] = rpc(ep, "eth_call", [{"to": A, "type": "0x4", "authorizationList": [], "gas": "0x100000"}, "latest"])
    r["latestBlock"] = {k: v for k, v in (rpc(ep, "eth_getBlockByNumber", ["latest", False]).get("result") or {}).items()
                        if k in ("number", "gasLimit", "baseFeePerGas", "stateRoot", "timestamp", "requestsHash",
                                 "blobGasUsed", "excessBlobGas", "parentBeaconBlockRoot", "withdrawalsRoot")}
    fp[ep] = r
out["forkprobe"] = fp

# HyperCore info: spot metadata and aligned quote info (L-1263)
info = {}
info["spotMeta"] = post(INFO, {"type": "spotMeta"})
for t in ["alignedQuoteTokenInfo", "alignedQuoteTokenStatus", "perpDexs"]:
    info[t] = post(INFO, {"type": t})
info["pmUserRole"] = post(INFO, {"type": "userRole", "user": PM.lower()})
info["pmSpotState"] = post(INFO, {"type": "spotClearinghouseState", "user": PM.lower()})
out["info"] = info
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("written")
