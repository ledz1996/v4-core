#!/bin/bash
# Cycle 31 theme-monad-gcc-real-states: every run behind the research file. Seeds are fixed in the scripts (3131).
# Nothing from the Monad package is executed: the gcc-build functions are interpreted from objdump text in the x86 model.
cd "$(dirname "$0")/.."
R=../../027/theme-monad-engine-agreement.work/out/pm-runtime.hex
python3 -I scripts/mkhook.py
scripts/build.sh > out/build-clang.log 2>&1
CXX=g++ scripts/build.sh > out/build-gcc.log 2>&1
build/clang/asmdump_orig $R out/asm-orig.txt; build/clang/asmdump_orig $R out/asm-orig2.txt
HX_STATELOG=out/states.jsonl build/clang/asmdump_hook $R out/asm-hook.txt
build/gcc/asmdump_orig $R out/asm-gcc13.txt; HX_STATELOG=out/states-gcc13.jsonl build/gcc/asmdump_hook $R out/asm-gcc13-hook.txt
python3 -I scripts/asmcmp.py out/asm-orig.txt out/asm-orig2.txt out/asm-hook.txt ../../027/theme-monad-engine-agreement.work/out/pm-asm-0.16.7.txt > out/asmcmp.txt
python3 -I scripts/asmcmp.py out/asm-orig.txt out/asm-orig2.txt out/asm-gcc13.txt out/asm-gcc13-hook.txt > out/asmcmp-gcc13.txt
python3 -I scripts/statecmp.py out/states.jsonl out/states-gcc13.jsonl > out/statecmp-gcc13.txt
python3 -I scripts/blockops.py out/states.jsonl out/value128-ops.json
python3 -I scripts/realshift.py out/model 2000
for f in lit-shl-bit-mask lit-shl-limb-index lit-shr-bit-mask push-top-index free-offset-stale state-dup-swap spill-offset-plus1 spill-store-missing shl-wrong-limb; do
  python3 -I scripts/realshift.py out/model 200 $f 2>&1 | head -1; done > out/model/faults.log
python3 -I scripts/task4.py
