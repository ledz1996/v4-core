import json, urllib.request, time
def call(url, method, params, timeout=60, retries=4):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    for i in range(retries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, body, {"content-type":"application/json","user-agent":"rpc-client"}), timeout=timeout)
            j = json.loads(r.read())
            if 'error' in j: 
                if i==retries-1: raise RuntimeError(j['error'])
                time.sleep(1+i); continue
            return j['result']
        except RuntimeError: raise
        except Exception as e:
            if i==retries-1: raise
            time.sleep(1+2*i)
def batch(url, reqs, timeout=120, retries=10):
    body = json.dumps([{"jsonrpc":"2.0","id":i,"method":m,"params":p} for i,(m,p) in enumerate(reqs)]).encode()
    for k in range(retries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, body, {"content-type":"application/json","user-agent":"rpc-client"}), timeout=timeout)
            j = json.loads(r.read())
            if isinstance(j, dict): raise RuntimeError(j)
            out=[None]*len(reqs)
            for x in j:
                if 'error' in x: raise RuntimeError(x['error'])
                out[x['id']]=x['result']
            return out
        except Exception as e:
            if k==retries-1: raise
            time.sleep(2+3*k)
