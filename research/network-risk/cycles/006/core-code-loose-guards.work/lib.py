# Shared helpers. Read-only JSON-RPC only.
import json, os, sys, time, requests
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from keccak import keccak256
NETS = json.load(open(os.path.join(HERE, '..', '..', '..', 'state', 'networks.json')))['networks']
S = requests.Session()
S.headers.update({'content-type': 'application/json', 'user-agent': 'curl/8'})
def post(url, payload, timeout=40, tries=4):
    last = None
    for i in range(tries):
        try:
            r = S.post(url, data=json.dumps(payload), timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                last = 'http %d %s' % (r.status_code, r.text[:160]); time.sleep(1.5 * (i + 1)); continue
            return r.json()
        except Exception as e:
            last = repr(e)[:200]; time.sleep(1.0 * (i + 1))
    return {'error': {'message': 'transport: ' + str(last)}}
def rpc(url, method, params, **kw):
    return post(url, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}, **kw)
def net(cid): return [n for n in NETS if n['chainId'] == cid][0]
def sel(sig): return keccak256(sig.encode())[:4].hex()
def w(x):
    if isinstance(x, str): return x[2:].lower().rjust(64, '0')
    return (x % (1 << 256)).to_bytes(32, 'big').hex()
def cd(sig, *args): return sel(sig) + ''.join(w(a) for a in args)
def pad32(h): return h + '0' * ((-len(h) // 2) % 32 * 2)
def item(target, data, value=0):
    return w(target) + w(value) + w(len(data) // 2) + pad32(data)
def script(flags, items): return w(flags) + ''.join(items)
def unlock(inner): return sel('unlock(bytes)') + w(0x20) + w(len(inner) // 2) + pad32(inner)
def records(hexdata):
    b = bytes.fromhex(hexdata[2:] if hexdata.startswith('0x') else hexdata); out = []; i = 0
    while i + 64 <= len(b):
        ok = int.from_bytes(b[i:i + 32], 'big'); n = int.from_bytes(b[i + 32:i + 64], 'big')
        if ok > 1 or n > len(b): out.append(('?', b[i:].hex())); break
        out.append((ok, b[i + 64:i + 64 + n].hex())); i += 64 + (n + 31) // 32 * 32
    return out
def delta_slot(target, currency): return '0x' + keccak256(bytes.fromhex(w(target)) + bytes.fromhex(w(currency))).hex()
IS_UNLOCKED = '0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23'
NONZERO = '0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b'
RESERVES = '0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95'
CURRENCY = '0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9'
ERR = {sel(s): s for s in ['ManagerLocked()', 'DelegateCallNotAllowed()', 'CurrencyNotSettled()', 'NonzeroNativeValue()', 'AlreadyUnlocked()', 'PoolNotInitialized()',
                           'InvalidCaller()', 'SafeCastOverflow()', 'MustClearExactPositiveDelta()', 'WrappedError(address,bytes4,bytes,bytes)', 'ProtocolFeeCurrencySynced()',
                           'SwapAmountCannotBeZero()', 'Error(string)', 'Panic(uint256)']}
def short(ok, data):
    d = data
    if not ok and d[:8] in ERR: return 'REVERT ' + ERR[d[:8]] + ('' if len(d) <= 8 else ' +%d bytes' % (len(d) // 2 - 4))
    if not ok: return 'REVERT 0x' + d[:72] + ('' if len(d) <= 72 else '..(%d bytes)' % (len(d) // 2))
    if len(d) == 64: return 'ok 0x' + d.lstrip('0') if d.strip('0') else 'ok 0'
    return 'ok (%d bytes) 0x%s' % (len(d) // 2, d[:72])
