import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe as p
names = {p.sel(x).hex(): x for x in ['CurrencyNotSettled()','AlreadyUnlocked()','ManagerLocked()','MustClearExactPositiveDelta()','SafeCastOverflow()','NonzeroNativeValue()','ProtocolFeeCurrencySynced()','InvalidCaller()','WrappedError(address,bytes4,bytes,bytes)']}
r = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'probe3_results.json')))
def recs(h):
    if not isinstance(h, str): return 'ERR ' + json.dumps(h)[:160]
    b = bytes.fromhex(h[2:])
    if not int.from_bytes(b[:32], 'big'): return 'outer-revert ' + names.get(b[32:36].hex(), b[32:68].hex())
    ln = int.from_bytes(b[64:96], 'big'); body = b[96:96+ln]; out = []
    for i in range(0, ln, 64):
        s = int.from_bytes(body[i:i+32], 'big'); wd = body[i+32:i+64]
        if s: out.append('ok:' + (wd.hex().lstrip('0') or '0'))
        else: out.append('revert:' + (names.get(wd[:4].hex(), wd[:4].hex()) if any(wd) else 'empty'))
    return out
ref = None
for cid, o in r.items():
    m = recs(o['main']); f = recs(o['fee']) if 'fee' in o else 'no controller'
    if ref is None: ref = m; print('REF main', cid, m)
    print(cid, o['name'], int(o['block'], 16), 'main', 'SAME' if m == ref else 'DIFF ' + json.dumps(m), '| fee', f)
