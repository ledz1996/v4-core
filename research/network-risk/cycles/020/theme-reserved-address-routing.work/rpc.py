import json,urllib.request,ssl,time
ctx=ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(url,method,params,timeout=60):
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    r=urllib.request.Request(url,body,{'content-type':'application/json','user-agent':'curl/8.5'})
    try:
        j=json.load(urllib.request.urlopen(r,timeout=timeout,context=ctx))
    except urllib.error.HTTPError as e:
        b=e.read()[:300].decode('latin1')
        return {'httperror':e.code,'body':('cloudflare challenge page' if 'Just a moment' in b else b[:120])}
    except Exception as e:
        return {'exception':str(e)[:300]}
    return j
