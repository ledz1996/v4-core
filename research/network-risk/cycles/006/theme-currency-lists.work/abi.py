# Small ABI encoder for argument templating in read-only simulations.
def split_types(sig):
    inner = sig[sig.index('(') + 1: sig.rindex(')')]
    out = []; depth = 0; cur = ''
    for ch in inner:
        if ch == ',' and depth == 0: out.append(cur); cur = ''
        else:
            if ch == '(': depth += 1
            if ch == ')': depth -= 1
            cur += ch
    if cur: out.append(cur)
    return out
def is_dynamic(t): return t in ('string', 'bytes') or t.endswith('[]')
def enc_static(t, v):
    if t == 'address': return int(v, 16).to_bytes(32, 'big')
    if t.startswith('uint') or t.startswith('int'):
        bits = int(t.lstrip('uint') or 256); return (int(v) % (1 << bits)).to_bytes(32, 'big')
    if t == 'bool': return int(bool(v)).to_bytes(32, 'big')
    if t.startswith('bytes'): return bytes(v).ljust(32, b'\0')
    raise ValueError(t)
def encode(types, vals):
    head = b''; tail = b''; hs = 0
    for t in types:
        if t.endswith(']') and not t.endswith('[]'):
            hs += 32 * int(t[t.rindex('[') + 1:-1])
        else: hs += 32
    for t, v in zip(types, vals):
        if t in ('string', 'bytes'):
            b = v if isinstance(v, bytes) else v.encode()
            head += (hs + len(tail)).to_bytes(32, 'big')
            tail += len(b).to_bytes(32, 'big') + b.ljust((len(b) + 31) // 32 * 32, b'\0')
        elif t.endswith('[]'):
            head += (hs + len(tail)).to_bytes(32, 'big')
            tail += len(v).to_bytes(32, 'big') + b''.join(enc_static(t[:-2], x) for x in v)
        elif t.endswith(']'):
            base = t[:t.rindex('[')]
            head += b''.join(enc_static(base, x) for x in v)
        else: head += enc_static(t, v)
    return (head + tail).hex()
def supported(types):
    for t in types:
        b = t
        if b.endswith(']'): b = b[:b.rindex('[')]
        if '(' in b or '[' in b: return False
        if not (b in ('address', 'bool', 'string', 'bytes') or b.startswith('uint') or b.startswith('int') or (b.startswith('bytes') and b[5:].isdigit())): return False
    return True
