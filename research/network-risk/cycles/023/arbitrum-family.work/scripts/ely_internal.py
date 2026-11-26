# Pull internal call lists touching the Elysium PoolManager from the explorer API in block windows,
# and check whether each transaction that has a take/settle/mint/burn/clear/settleFor frame also has an unlock frame.
import json, sys, urllib.request, ssl, time, collections
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
PM = "0xe2e105d3f7209a9da11f83ccf3e7398a753823f1"
B = "https://elysium.kinetiq.xyz/explorer/api"
SEL = {"48c89491": "unlock", "0b0d9c09": "take", "11da60b4": "settle", "3dd45adb": "settleFor", "156e29f6": "mint",
       "f5298aca": "burn", "80f0b44c": "clear", "a5841194": "sync", "f3cd914c": "swap", "5a6bcfda": "modifyLiquidity",
       "234266d7": "donate", "6276cbbe": "initialize"}
def get(u):
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "curl/8"}), timeout=90, context=CTX))
        except Exception as e:
            time.sleep(3)
    return {"result": None, "message": "fail"}
start, end, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
out = sys.argv[4]
rows = []; windows = []
b = start
while b < end:
    e = min(end, b + step - 1); page = 1
    while True:
        r = get(f"{B}?module=account&action=txlistinternal&address={PM}&startblock={b}&endblock={e}&page={page}&offset=1000&sort=asc")
        res = r.get("result")
        if not isinstance(res, list):
            windows.append([b, e, page, "error", str(r.get("message"))[:80] + " " + str(res)[:80]]); break
        rows += res; windows.append([b, e, page, len(res)])
        if len(res) < 1000: break
        page += 1
    b = e + 1
bytx = collections.defaultdict(list)
for x in rows:
    bytx[x["hash"]].append(x)
kinds = collections.Counter(); zero_val = 0; failed = 0
orphans = []
for h, fr in bytx.items():
    names = set()
    for x in fr:
        s = x.get("input", "")[2:10]
        n = SEL.get(s, s if x["to"].lower() == PM else "out:" + (s or "value"))
        kinds[n] += 1
        if x["to"].lower() == PM: names.add(n)
        if x.get("value") == "0": zero_val += 1
        if x.get("isError") == "1": failed += 1
    if names & {"take", "settle", "settleFor", "mint", "burn", "clear"} and "unlock" not in names:
        orphans.append([h, sorted(names)])
json.dump({"range": [start, end], "rows": len(rows), "txs": len(bytx), "zeroValueFrames": zero_val, "failedFrames": failed,
           "kinds": kinds.most_common(), "txsWithSettlementFrameButNoUnlockFrame": len(orphans), "orphanSample": orphans[:50],
           "windows": windows}, open(out, "w"), indent=1)
print(len(rows), len(bytx), zero_val, failed, kinds.most_common(15), len(orphans))
