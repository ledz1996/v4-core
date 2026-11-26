import json,urllib.request,time,sys
def call(url,method,params,retries=6):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    for i in range(retries):
        try:
            req=urllib.request.Request(url,body,{"content-type":"application/json","user-agent":"rpc-client/1.0"})
            r=json.load(urllib.request.urlopen(req,timeout=120))
            if 'error' in r and 'rate' in r['error'].get('message','').lower():
                time.sleep(2*(i+1)); continue
            return r
        except Exception as e:
            err=str(e); time.sleep(2*(i+1))
    return {"error":{"message":"failed after retries"}}
