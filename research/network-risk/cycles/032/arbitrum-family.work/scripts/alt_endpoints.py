# Cycle 32: run the battery and targeted vectors against second Elysium endpoints (Conduit mainnet RPC, dRPC).
import sys, json, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery, targeted
urls = sys.argv[2:]
out = {}
def cv(u):
    r = urllib.request.Request(u, data=json.dumps({"jsonrpc":"2.0","id":1,"method":"web3_clientVersion","params":[]}).encode(), headers={"content-type":"application/json","user-agent":"curl/8"})
    try: return json.loads(urllib.request.urlopen(r, timeout=30).read()).get('result')
    except Exception as e: return 'ERR ' + str(e)[:80]
for u in urls:
    rec = {'clientVersionBefore': cv(u)}
    code = battery.dispatcher()
    for name, V in (('battery', battery.vectors()), ('targeted', targeted.vectors())):
        done, bad, errors = battery.run(u, code, V)
        rec[name] = {'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:50], 'errors': errors[:5]}
        print(u, name, len(V), done, len(bad), len(errors), flush=True)
    rec['clientVersionAfter'] = cv(u)
    out[u] = rec
json.dump(out, open(sys.argv[1], 'w'), indent=1)
