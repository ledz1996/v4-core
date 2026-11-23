import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak256
def sel(s):
    r = keccak256(s.encode()); r = r if isinstance(r,(bytes,bytearray)) else bytes.fromhex(r)
    return r[:4].hex()
names = {sel(x): x for x in ['CurrencyNotSettled()','AlreadyUnlocked()','ManagerLocked()','MustClearExactPositiveDelta()','SafeCastOverflow()','NonzeroNativeValue()']}
names['4e487b71'] = 'Panic(uint256)'
print(names)
r = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw','probe_results.json')))
def short(v):
    if isinstance(v, dict):
        e = v.get('error') or {}
        d = e.get('data') if isinstance(e, dict) else None
        if isinstance(d, str) and d.startswith('0x'):
            return 'revert:' + (names.get(d[2:10], d[:18]) if len(d) > 2 else 'empty')
        return 'ERR:' + json.dumps(e)[:90]
    return v
def records(hexstr):
    b = bytes.fromhex(hexstr[2:])
    ok = int.from_bytes(b[:32], 'big')
    if not ok:
        return ('outer-revert', names.get(b[32:36].hex(), b[32:].hex()[:16] or 'empty'))
    ln = int.from_bytes(b[64:96], 'big'); body = b[96:96+ln]
    out = []
    for i in range(0, ln, 64):
        s = int.from_bytes(body[i:i+32], 'big'); word = body[i+32:i+64]
        out.append('ok' if s else 'revert:' + (names.get(word[:4].hex(), word[:4].hex()) if any(word) else 'empty'))
    return ('outer-ok', out)
ref = None
for cid, o in r.items():
    codes = [len(v or '0x') for v in o['codeAt'].values()]
    locked = {k: short(v) for k, v in o['locked'].items()}
    seq = {}
    for k, v in o['seq'].items():
        seq[k] = records(v) if isinstance(v, str) else short(v)
    sig = json.dumps([locked, seq], sort_keys=True)
    if ref is None: ref = sig; print('REFERENCE', cid, json.dumps(locked), json.dumps(seq, indent=0))
    print(cid, o['name'], 'block', int(o['block'],16) if o['block'] else None, 'helperCodeLens', codes, 'SAME' if sig == ref else 'DIFF')
    if sig != ref: print('   ', json.dumps(locked)); print('   ', json.dumps(seq))
