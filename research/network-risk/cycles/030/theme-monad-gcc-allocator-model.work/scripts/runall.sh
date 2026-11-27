#!/bin/bash
# Cycle 30: every run behind theme-monad-gcc-allocator-model.research.json (seeds are fixed inside the scripts).
# Nothing from the Monad package is executed: the scripts interpret objdump text of it in the x86 model.
cd "$(dirname "$0")/.."
python3 -I scripts/varsites.py out
python3 -I scripts/shiftvar.py out/run 3000 120 > out/run/shiftvar.log 2>&1
python3 -I scripts/shiftvar.py out/run 2000 60 - perm
python3 -I scripts/shiftfull.py out/run 6000 100 > out/run/shiftfull.log 2>&1
python3 -I scripts/shiftfull.py out/run 2000 50 - perm
python3 -I scripts/wfso.py out/run 3000 20
python3 -I scripts/aorel.py out/run 4000
python3 -I scripts/prologue.py out/run
python3 -I scripts/rodata.py out/run
python3 -I scripts/rodata.py out/run eq-low-half
python3 -I scripts/cmpclang.py out 3000
for f in swap-rax-rcx shl-wrong-limb shl-dst-copy-swap spill-store-missing spill-slot-scale spill-limb-stride \
         spill-offset-plus1 rodata-shared-label avx-spill-store-missing shr-avx-dword-bound; do
  python3 -I scripts/shiftvar.py out/run 600 30 $f 2>&1 | head -1
  python3 -I scripts/shiftfull.py out/run 900 30 $f 2>&1 | head -1
done > out/run/faults.log
for a in 381b0d 381dd1 381e57 381ea8 381f43 382118 382190 3822ba 382656; do
  python3 -I scripts/wfso.py out/run 400 5 wfso-drop-$a 2>&1 | head -1
done > out/run/faults-wfso.log
