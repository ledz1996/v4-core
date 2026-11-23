# Function selectors found in the dispatcher of each approved contract, by code group; names from the openchain signature database.
import sys, json, os, requests
from lib import *
from state import url, bcall
def selectors(code):
    b = bytes.fromhex(code[2:]); out = []; i = 0
    while i < len(b):
        op = b[i]
        if op == 0x63 and i + 5 < len(b) and b[i + 5] in (0x14, 0x81, 0x11, 0x10, 0x90) :
            s = b[i + 1:i + 5].hex()
            if s not in out and s not in ('ffffffff',): out.append(s)
        i += 1 + (op - 0x5f if 0x60 <= op <= 0x7f else 0)
    return out
CACHE = os.path.join(HERE, 'raw', 'sigcache.json')
sc = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def names(sels):
    need = [s for s in sels if s not in sc]
    for i in range(0, len(need), 40):
        part = need[i:i + 40]
        try:
            j = requests.get('https://api.openchain.xyz/signature-database/v1/lookup', params={'function': ','.join('0x' + s for s in part), 'filter': 'true'}, timeout=30).json()
            for s in part:
                r = (j.get('result', {}).get('function', {}) or {}).get('0x' + s) or []
                sc[s] = [x['name'] for x in r][:2]
        except Exception as e:
            for s in part: sc.setdefault(s, ['?lookup failed'])
    json.dump(sc, open(CACHE, 'w'))
    return {s: sc.get(s) for s in sels}
def code_of(cid, x):
    st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid)))
    d = st['info'].get(x, {})
    tgt = d.get('delegate') or x
    return rpc(url(cid), 'eth_getCode', [tgt, 'latest'])
if __name__ == '__main__':
    cid = int(sys.argv[1])
    for x in sys.argv[2:]:
        c = code_of(cid, x); s = selectors(c); nm = names(s)
        print('==', cid, x, 'len', len(c) // 2 - 1, 'PM addr in code', net(cid)['poolManager'][2:].lower() in c.lower(), 'transferFrom sel', 'fe99049a' in c, 'burn sel', 'f5298aca' in c, 'mint sel', '156e29f6' in c, 'setOperator', '558a7297' in c)
        print('   ', '; '.join('%s %s' % (k, (v or ['?'])[0]) for k, v in nm.items()))
