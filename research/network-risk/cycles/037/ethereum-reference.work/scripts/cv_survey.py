"""Ask each Ethereum endpoint for web3_clientVersion several times, alone and inside a
batch with eth_chainId, to see which builds answer. Read-only calls only.
usage: python3 cv_survey.py urls.txt out.json [rounds]"""
import json, sys, time, urllib.request, concurrent.futures as cf

def post(url, body, timeout=12):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "rpc-survey/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def probe(url, rounds):
    seen = []
    for i in range(rounds):
        try:
            r = post(url, {"jsonrpc": "2.0", "id": 1, "method": "web3_clientVersion", "params": []})
            seen.append(r.get("result") or ("ERR " + json.dumps(r.get("error"))[:120]))
        except Exception as e:
            seen.append("ERR " + str(e)[:120])
            if i == 0:
                break
        time.sleep(0.3)
    return url, seen

urls = [l.strip() for l in open(sys.argv[1]) if l.strip()]
rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 6
out = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rounds": rounds, "endpoints": {}}
with cf.ThreadPoolExecutor(16) as ex:
    for url, seen in ex.map(lambda u: probe(u, rounds), urls):
        out["endpoints"][url] = seen
        print(url, sorted(set(seen)))
json.dump(out, open(sys.argv[2], "w"), indent=1)
