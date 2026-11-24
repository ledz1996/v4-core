import json,sys,urllib.request,time,os
os.environ.setdefault('SSL_CERT_FILE','/root/.ccr/ca-bundle.crt')
def rpc(url,method,params,timeout=40,retries=2):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for i in range(retries+1):
        try:
            req=urllib.request.Request(url,data=body,headers={'content-type':'application/json','user-agent':'curl/8'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            last={'error':str(e)[:300]}
            time.sleep(1)
    return last
