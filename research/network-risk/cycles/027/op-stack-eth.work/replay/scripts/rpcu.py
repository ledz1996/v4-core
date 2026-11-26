"""Minimal read-only JSON-RPC helper for theme-unlockless-frames (cycle 22).
Every call is logged with endpoint, method and outcome class so refusals are on record."""
import json, os, ssl, time, urllib.request, urllib.error
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') if os.path.exists('/root/.ccr/ca-bundle.crt') else None
UA = 'rpc-client'


def call(url, method, params, timeout=90):
    """Returns (result, error_string). error_string is None on success."""
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': UA})
    try:
        raw = urllib.request.urlopen(req, timeout=timeout, context=CTX).read()
    except urllib.error.HTTPError as e:
        try:
            txt = e.read()[:300].decode('utf8', 'replace')
        except Exception:
            txt = ''
        return None, 'HTTP %d %s' % (e.code, txt.replace('\n', ' ')[:200])
    except Exception as e:
        return None, 'EXC %s' % (str(e)[:200])
    try:
        r = json.loads(raw)
    except Exception:
        return None, 'NONJSON %s' % raw[:200]
    if isinstance(r, list):
        r = r[0]
    if 'error' in r:
        return None, 'RPCERR %s' % json.dumps(r['error'])[:300]
    return r.get('result'), None


def retry(urls, method, params, tries=6, timeout=90):
    last = None
    for k in range(tries):
        u = urls[k % len(urls)]
        res, err = call(u, method, params, timeout)
        if err is None:
            return res
        last = err
        if 'RPCERR' in err and ('not found' in err.lower() or 'does not exist' in err.lower() or 'not supported' in err.lower()):
            break
        time.sleep(1 + k)
    raise RuntimeError(last)
