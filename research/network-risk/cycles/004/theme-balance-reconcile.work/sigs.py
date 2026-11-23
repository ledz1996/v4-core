# List PUSH4 selectors found in a contract's runtime code and look them up in a public signature database. Read only.
import sys, json, requests
from lib import *
from config import CFG
def selectors(code):
    b = bytes.fromhex(code[2:]); out = []; i = 0
    while i < len(b):
        op = b[i]
        if op == 0x63 and i + 4 < len(b):
            s = b[i + 1:i + 5].hex()
            # dispatcher pattern: PUSH4 sel, EQ / DUP, or (GT/LT for binary search)
            if b[i + 5] in (0x14, 0x81, 0x11, 0x10, 0x85, 0x82) and s not in out: out.append(s)
            i += 5
        elif 0x60 <= op <= 0x7f: i += op - 0x5e
        else: i += 1
    return out
def lookup(sels):
    out = {}
    for i in range(0, len(sels), 40):
        q = ','.join('0x' + s for s in sels[i:i + 40])
        try:
            j = requests.get('https://api.openchain.xyz/signature-database/v1/lookup', params={'function': q, 'filter': 'true'}, timeout=30, headers={'user-agent': 'curl/8'}).json()
            for k, v in (j.get('result', {}).get('function') or {}).items(): out[k[2:]] = [x['name'] for x in (v or [])][:2]
        except Exception as e:
            out['err'] = str(e)[:100]
    return out
if __name__ == '__main__':
    cid = int(sys.argv[1]); a = sys.argv[2]; u = CFG[cid]['state'][0]
    code = rpc(u, 'eth_getCode', [a, 'latest']); s = selectors(code); l = lookup(s)
    print(len(code) // 2 - 1, 'bytes', len(s), 'selectors')
    print(' '.join('%s=%s' % (x, (l.get(x) or ['?'])[0]) for x in s))
