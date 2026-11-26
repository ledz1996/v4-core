import json, urllib.request, time
def rpc(url, method, params, timeout=60, tries=4):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    last=None
    for k in range(tries):
        try:
            req=urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'review-client/1.0'})
            r=json.loads(urllib.request.urlopen(req,timeout=timeout).read())
            if 'error' in r: raise RuntimeError(json.dumps(r['error'])[:300])
            return r['result']
        except RuntimeError: raise
        except Exception as e:
            last=e; time.sleep(2*(k+1))
    raise last
def batch(url, calls, timeout=90):
    body=json.dumps([{'jsonrpc':'2.0','id':i,'method':m,'params':p} for i,(m,p) in enumerate(calls)]).encode()
    req=urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'review-client/1.0'})
    r=json.loads(urllib.request.urlopen(req,timeout=timeout).read())
    r=sorted(r,key=lambda x:x['id'])
    return [x.get('result', {'__error':x.get('error')}) for x in r]
