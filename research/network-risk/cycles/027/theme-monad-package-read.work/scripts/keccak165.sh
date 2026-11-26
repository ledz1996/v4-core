#!/bin/bash
# Disassemble the keccak routines of the 0.16.5 package and of the 0.16.5 harness object, normalise, compare.
W=/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work
P5=$W/dl/p165/data/usr/local/bin/monad
H5=/home/user/v4-core/research/network-risk/cycles/023/theme-monad-compiled-coverage.work/build/0.16.5-plain/category_crypto_keccak_impl.S.o
H7=/home/user/v4-core/research/network-risk/cycles/023/theme-monad-compiled-coverage.work/build/0.16.7-plain/category_crypto_keccak_impl.S.o
A=$(grep -E " t __KeccakF1600$" $W/out/nm-monad-0.16.5.txt | awk '{print $1}')
SA=$(grep -E " T SHA3_squeeze$" $W/out/nm-monad-0.16.5.txt | awk '{print $1}')
SS=$(grep -E " T SHA3_squeeze$" $W/out/nm-monad-0.16.5.txt | awk '{print $2}')
END=$((0x$SA + 0x$SS))
objdump -d -M intel --no-show-raw-insn --start-address=0x$A --stop-address=$END $P5 | tail -n +7 | python3 -I -c '
import sys,re
for l in sys.stdin:
    l=re.sub(r"^\s*[0-9a-f]+:\s*","",l.rstrip()); l=re.sub(r"[0-9a-f]+ <[^>]*>","",l); print(l)' > $W/out/keccak-pkg165.s
objdump -d -M intel --no-show-raw-insn $H5 | tail -n +7 | python3 -I -c '
import sys,re
for l in sys.stdin:
    l=re.sub(r"^\s*[0-9a-f]+:\s*","",l.rstrip()); l=re.sub(r"[0-9a-f]+ <[^>]*>","",l); print(l)' > $W/out/keccak-harness165.s
python3 -I $W/scripts/normcomm.py $W/out/keccak-pkg165.s > $W/out/keccak-pkg165.n
python3 -I $W/scripts/normcomm.py $W/out/keccak-harness165.s > $W/out/keccak-harness165.n
echo "harness 0.16.5 vs package 0.16.5:"; diff $W/out/keccak-harness165.n $W/out/keccak-pkg165.n
echo "package 0.16.5 vs package 0.16.7:"; diff $W/out/keccak-pkg165.n $W/out/keccak-pkg.n && echo same
cmp $H5 $H7 && echo "harness objects 0.16.5 and 0.16.7 identical"
