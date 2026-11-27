"""Dump named functions of the Nitro b72783f release binaries (cycle 30 extraction, read as data with objdump only)."""
import sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/031/theme-go-family-binary-lift.work/scripts')
import goshim as G
D = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/dl/'


def relabel(text, fns):
    """objdump of the stripped binary labels everything crosscall2@@Base+off; put the pclntab names back."""
    import bisect, re
    starts = sorted((v[0], v[1], k) for k, v in fns.items())
    keys = [s[0] for s in starts]

    def name(a):
        i = bisect.bisect_right(keys, a) - 1
        if i >= 0 and starts[i][0] <= a < starts[i][1]:
            off = a - starts[i][0]
            return starts[i][2] + ('+0x%x' % off if off else '')
        return None

    def sub(m):
        a = int(m.group(1), 16)
        n = name(a)
        return '%s <%s>' % (m.group(1), n) if n else m.group(0)
    return re.sub(r'([0-9a-f]+) <[^>]+>', sub, text)


if __name__ == '__main__':
    arch, pat, out = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
    fns = G.fnlist(D + 'build/all-%s.txt' % arch)
    sel = [n for n in fns if any(n.endswith(p) for p in pat)]
    open(out, 'w').write(relabel(G.disasm(D + '%s/usr/local/bin/nitro' % arch, arch, [fns[n] for n in sel]), fns))
    print(len(sel)); [print(' ', n, hex(fns[n][0])) for n in sel]
