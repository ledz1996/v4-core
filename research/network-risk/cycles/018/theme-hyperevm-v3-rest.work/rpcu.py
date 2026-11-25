import json, urllib.request, time, os, ssl
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
def rpc(url, method, params, timeout=60, tries=6):
    last=None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(), {'content-type':'application/json','user-agent':'rpc-client'})
            r = json.loads(urllib.request.urlopen(req, timeout=timeout, context=CTX).read())
            if 'error' in r:
                msg=str(r['error'])
                if 'revert' in msg.lower() or 'execution' in msg.lower(): raise ValueError(msg)
                last=RuntimeError(msg); 
                if any(x in msg.lower() for x in ('range','limit','too many','exceed')): raise last
                time.sleep(1+k); continue
            return r['result']
        except ValueError: raise
        except RuntimeError as e:
            if any(x in str(e).lower() for x in ('range','limit','too many','exceed')): raise
            last=e; time.sleep(1+k)
        except Exception as e:
            last=e; time.sleep(1+k)
    raise last
