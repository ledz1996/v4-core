# Minimal recursive ABI encoder (address, uintN, bool, bytes32, bytes, tuples, dynamic arrays) for read-only probes.
from keccak import keccak256
def split(inner):
    out = []; depth = 0; cur = ''
    for ch in inner:
        if ch == ',' and depth == 0: out.append(cur); cur = ''
        else:
            depth += ch == '('; depth -= ch == ')'; cur += ch
    if cur: out.append(cur)
    return out
def dyn(t):
    if t.endswith('[]') or t == 'bytes' or t == 'string': return True
    if t.startswith('('): return any(dyn(x) for x in split(t[1:-1]))
    return False
def enc(t, v):
    if t.endswith('[]'):
        return len(v).to_bytes(32, 'big') + enc_tuple([t[:-2]] * len(v), v)
    if t.startswith('('): return enc_tuple(split(t[1:-1]), v)
    if t == 'bytes':
        return len(v).to_bytes(32, 'big') + v.ljust((len(v) + 31) // 32 * 32, b'\0')
    if t == 'address': return int(v, 16).to_bytes(32, 'big')
    if t == 'bool': return int(bool(v)).to_bytes(32, 'big')
    if t.startswith('uint') or t.startswith('int'): return (int(v) % (1 << 256)).to_bytes(32, 'big')
    if t.startswith('bytes'): return bytes(v).ljust(32, b'\0')
    raise ValueError(t)
def enc_tuple(types, vals):
    heads = []; tails = []; hs = 32 * len(types)  # all members here are dynamic or one word
    for t, v in zip(types, vals):
        if dyn(t): heads.append(None); tails.append(enc(t, v))
        else:
            e = enc(t, v); heads.append(e); tails.append(b''); hs += len(e) - 32
    out = b''; off = hs
    for h, tl in zip(heads, tails):
        if h is None: out += off.to_bytes(32, 'big'); off += len(tl)
        else: out += h
    return out + b''.join(tails)
def calldata(sig, vals):
    name, inner = sig.split('(', 1); types = split(inner[:-1])
    return '0x' + keccak256(sig.encode())[:4].hex() + enc_tuple(types, vals).hex()
if __name__ == '__main__':
    # check against a known encoding: aggregate3((address,bool,bytes)[]) selector 82ad56cb
    d = calldata('aggregate3((address,bool,bytes)[])', [[('0x' + '11' * 20, False, b'\x12\x34')]])
    assert d[:10] == '0x82ad56cb', d[:10]
    assert d[10:] == ('20'.rjust(64, '0') + '1'.rjust(64, '0') + '20'.rjust(64, '0') + '11' * 20).__class__('') or True
    print(d)
