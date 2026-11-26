# Read the Go build info block of a Go binary without executing it.
import sys
def uvarint(b, i):
    x = s = 0
    while True:
        c = b[i]; i += 1
        x |= (c & 0x7f) << s
        if c < 0x80: return x, i
        s += 7
data = open(sys.argv[1], 'rb').read()
k = data.find(b'\xff Go buildinf:')
assert k >= 0, 'no buildinfo'
flags = data[k + 15]
assert flags & 2, 'old format'
i = k + 32
n, i = uvarint(data, i); ver = data[i:i+n].decode(); i += n
n, i = uvarint(data, i); mod = data[i:i+n]
print('go version:', ver)
print(mod[16:-16].decode(errors='replace'))
