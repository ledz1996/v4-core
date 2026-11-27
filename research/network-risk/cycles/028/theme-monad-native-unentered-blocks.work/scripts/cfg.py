"""Static successors of PoolManager IR blocks: fall through, and a JUMP/JUMPI whose target is pushed by the
instruction right before it. A JUMP with a computed target (a return) ends the walk. func(entry) returns every block
reachable from entry in this way, which for an internal function of the via-IR build is its body."""
import blocks as B
TERM = {0x00, 0x56, 0xf3, 0xfd, 0xfe, 0xff}
def succ(sp, offs_sorted, a):
    s = sp[a]; last = s[-1]; o = B.code[last]; out = []
    prev = s[-2] if len(s) > 1 else None
    tgt = None
    if prev is not None and 0x60 <= B.code[prev] <= 0x7f and o in (0x56, 0x57):
        tgt = int.from_bytes(B.code[prev + 1:last], 'big')
    if o == 0x57:
        if tgt is not None: out.append(tgt)
        else: out.append('dyn')
    if o == 0x56: out.append(tgt if tgt is not None else 'ret')
    if o not in TERM:
        i = offs_sorted.index(a)
        if i + 1 < len(offs_sorted): out.append(offs_sorted[i + 1])
    return out
def func(sp, entry):
    offs = sorted(sp); seen = []; st = [entry]; ends = set()
    while st:
        a = st.pop()
        if a in seen: continue
        if a not in sp: ends.add(('notblock', a)); continue
        seen.append(a)
        for t in succ(sp, offs, a):
            if isinstance(t, str): ends.add((t, a))
            else: st.append(t)
    return sorted(seen), ends
