#!/bin/sh
# Cycle 34 theme-monad-gcc-inlined-storage-sites: regenerate out/ (run from the work directory)
set -e
python3 -I scripts/sites.py out/sites.json > out/sites.log
python3 -I scripts/inl.py out 2000 > out/inl.log 2>&1
for f in key-from-element-below key-value-swapped live-gp-not-spilled live-avx-not-spilled result-written-to-other-slot hash-length-from-wrong-element deferred-comparison-lost arm-wrong-runtime-fn; do
  python3 -I scripts/inl.py out 200 $f > out/inl-$f.log 2>&1
done
SYNDC=1 python3 -I scripts/inl.py out 2000 > out/inl-syndc.log 2>&1
SYNDC=1 python3 -I scripts/inl.py out 200 deferred-comparison-lost > out/inl-syndc-deferred-comparison-lost.log 2>&1
python3 -I scripts/blk.py out 20000 > out/blk.log 2>&1
ONLY=0xd1f python3 -I scripts/blk.py out 20000 > out/blk-0xd1f.log 2>&1
python3 -I scripts/blk.py out 2000 stub-result-inverted > out/blk-stub-result-inverted.log 2>&1
python3 -I scripts/blk.py out 2000 live-gp-not-spilled > out/blk-live-gp-not-spilled.log 2>&1
# Task 4 (L-1253)
python3 -I scripts/mkhook.py
scripts/build.sh > out/build34.log 2>&1
R=../../027/theme-monad-engine-agreement.work/out/pm-runtime.hex
HX_STATELOG=out/states34.jsonl build/clang/asmdump_hook34 $R out/asm-hook34.txt
C31=../../031/theme-monad-gcc-real-states.work
python3 -I $C31/scripts/asmcmp.py $C31/out/asm-orig.txt $C31/out/asm-orig2.txt out/asm-hook34.txt ../../027/theme-monad-engine-agreement.work/out/pm-asm-0.16.7.txt > out/asmcmp34.txt
python3 -I scripts/tablecmp.py out/tablecmp.json
LOGTAB=1 python3 -I scripts/inl.py out 2000 > out/inl-logtab.log 2>&1
python3 -I scripts/logtab.py term out/logtab 2000 > out/logtab-term.log 2>&1
python3 -I scripts/logtab.py block out/logtab 3000 > out/logtab-block.log 2>&1
python3 -I scripts/logtab.py task3 out/logtab 2000 > out/logtab-task3.log 2>&1
python3 -I scripts/logtab.py realarith out/logtab 2000 > out/logtab-realarith.log 2>&1
TASK4=1 python3 -I scripts/logtab.py realarith out/logtab 2000 > out/logtab-realother.log 2>&1
KINDS=SGT,SLT TASK4=1 python3 -I scripts/logtab.py realarith out/logtab 2000 > out/logtab-realother-sgt-slt.log 2>&1
python3 -I scripts/write_research.py
