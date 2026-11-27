"""Find rip-relative instructions whose memory operand is a given GOT slot: call/jmp [rip+d] (ff 15/25) and
mov r64,[rip+d] (REX.W 8b, modrm with rm=101). Reads only. usage: python3 -I gotrefs.py <bin> <slot>..."""
import sys, struct
fb = open(sys.argv[1], 'rb').read()
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x20c7b00, 0x20c6b00, 0x4ea2a18
d = TEXT_VA - TEXT_OFF
for s in [int(x, 16) for x in sys.argv[2:]]:
    hits = []
    i = TEXT_OFF
    end = TEXT_OFF + TEXT_SZ
    # 2-byte opcode ff15/ff25 then disp32; instr len 6
    for pre, ln, name in ((b'\xff\x15', 6, 'call'), (b'\xff\x25', 6, 'jmp')):
        i = TEXT_OFF
        while True:
            i = fb.find(pre, i, end)
            if i < 0: break
            if i + d + ln + struct.unpack_from('<i', fb, i + 2)[0] == s: hits.append((name, hex(i + d)))
            i += 1
    for rex in (0x48, 0x4c):
        i = TEXT_OFF
        pat = bytes([rex, 0x8b])
        while True:
            i = fb.find(pat, i, end)
            if i < 0: break
            m = fb[i + 2]
            if m & 0xc7 == 0x05 and i + d + 7 + struct.unpack_from('<i', fb, i + 3)[0] == s: hits.append(('mov', hex(i + d)))
            i += 1
    print(hex(s), hits)
