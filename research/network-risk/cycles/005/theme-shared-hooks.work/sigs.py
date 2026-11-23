# List PUSH4 constants of a contract's code and look them up in public signature databases. Read-only.
import sys, json, requests
from lib import *
from config import CFG
def push4(code):
    b = bytes.fromhex(code[2:]); i = 0; out = []
    while i < len(b):
        op = b[i]
        if 0x60 <= op <= 0x7f:
            n = op - 0x5f
            if n == 4: out.append(b[i + 1:i + 5].hex())
            i += n
        i += 1
    seen = []; [seen.append(x) for x in out if x not in seen]
    return seen
def lookup(sels):
    res = {}
    for k in range(0, len(sels), 40):
        part = sels[k:k + 40]
        try:
            q = ','.join('0x' + s for s in part)
            r = requests.get('https://api.openchain.xyz/signature-database/v1/lookup?function=%s&filter=true' % q, timeout=30).json()
            for s, v in (r.get('result', {}).get('function') or {}).items():
                if v: res[s[2:]] = v[0]['name']
        except Exception as e: res['_err'] = repr(e)[:80]
    return res
if __name__ == '__main__':
    cid = int(sys.argv[1]); a = sys.argv[2]
    n = net(cid); code = None
    for u in [n['rpc']] + CFG[cid]['state']:
        try: code = rpc(u, 'eth_getCode', [a, 'latest']); break
        except Exception: pass
    s = push4(code); r = lookup(s)
    print(len(code) // 2 - 1, 'bytes;', len(s), 'push4 constants')
    for x in s: print('  ', x, r.get(x, ''))
