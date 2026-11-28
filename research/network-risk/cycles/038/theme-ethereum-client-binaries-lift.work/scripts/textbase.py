"""Finds runtime.firstmoduledata by the pointer to .gopclntab and prints minpc and text, read as data only. usage: textbase.py bin"""
import sys, struct
f = open(sys.argv[1], 'rb').read()
shoff, = struct.unpack_from('<Q', f, 0x28); se, sn, six = struct.unpack_from('<HHH', f, 0x3a)
secs = [struct.unpack_from('<IIQQQQ', f, shoff + i * se) for i in range(sn)]
stro = secs[six][4]
nm = lambda s: f[stro + s[0]:f.index(b'\0', stro + s[0])].decode()
S = {nm(s): s for s in secs}
pc = S['.gopclntab'][3]
key = struct.pack('<Q', pc)
for n in [k for k in S if S[k][1] != 8 and S[k][5] > 0]:
    s = S[n]; blob = f[s[4]:s[4] + s[5]]
    i = blob.find(key)
    while i >= 0:
        w = struct.unpack_from('<24Q', blob, i)
        print(n, hex(s[3] + i), 'minpc', hex(w[20]), 'maxpc', hex(w[21]), 'text', hex(w[22]), 'etext', hex(w[23]))
        i = blob.find(key, i + 8)
