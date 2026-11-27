"""Compare the CRYPTOGAMS keccak block (__KeccakF1600 to the end of the iotas table) of two ELF files byte for byte.
usage: python3 -I kblock.py <binA> <startA hex> <binB> <startB hex> <length hex>. Reads only."""
import sys, struct, hashlib
def rd(p, va, n):
    fb = open(p, 'rb').read(); phoff = struct.unpack_from('<Q', fb, 0x20)[0]; k = struct.unpack_from('<H', fb, 0x38)[0]
    for i in range(k):
        t, fl, off, v, pa, fs, ms, al = struct.unpack_from('<IIQQQQQQ', fb, phoff + 56 * i)
        if t == 1 and v <= va and va + n <= v + fs: return fb[off + va - v: off + va - v + n]
    raise SystemExit('not in a PT_LOAD segment')
a = rd(sys.argv[1], int(sys.argv[2], 16), int(sys.argv[5], 16)); b = rd(sys.argv[3], int(sys.argv[4], 16), int(sys.argv[5], 16))
d = [i for i in range(len(a)) if a[i] != b[i]]
print('len', len(a), 'sha256 A', hashlib.sha256(a).hexdigest()[:16], 'B', hashlib.sha256(b).hexdigest()[:16], 'differing bytes', len(d), [hex(x) for x in d[:10]])
