# Wrap the raw text segment (vaddr 0x120000000) in an ELF64 big-endian MIPS file with one .text section, for llvm-objdump.
import sys,struct
t=open(sys.argv[1],'rb').read(); BASE=0x120000000
shstr=b'\0.text\0.shstrtab\0'
off_text=64; off_str=off_text+len(t); off_sh=(off_str+len(shstr)+7)&~7
eh=b'\x7fELF'+bytes([2,2,1,0])+b'\0'*8+struct.pack('>HHIQQQIHHHHHH',2,8,1,BASE,0,off_sh,0x80000000|0x20000000|0x4,64,56,0,64,3,2)
sh0=b'\0'*64
sh1=struct.pack('>IIQQQQIIQQ',1,1,6,BASE,off_text,len(t),0,0,4,0)
sh2=struct.pack('>IIQQQQIIQQ',7,3,0,0,off_str,len(shstr),0,0,1,0)
out=eh+t+shstr; out+=b'\0'*(off_sh-len(out))+sh0+sh1+sh2
open(sys.argv[2],'wb').write(out)
