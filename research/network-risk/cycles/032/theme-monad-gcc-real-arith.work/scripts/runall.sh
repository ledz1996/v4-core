#!/bin/bash
# Cycle 32 theme-monad-gcc-real-arith: every run behind the research file. Seeds: 3232 (stream runs), 3233 (helpers).
# Nothing from the Monad package is executed: gcc-build functions are interpreted from the cycle 27 objdump text of
# /usr/local/bin/monad 0.16.7 (sha256 b7b4b242...5676, from monad_0.16.7_amd64.deb sha256 3cb9dba5...81fb) in the x86 model.
cd "$(dirname "$0")/.."
python3 -I scripts/fnindex.py out/fnindex.json
STOP=3a3ea0,375c50,3810b0,373800,3ad360,131ad0,3a3860 python3 -I scripts/closure.py 3838e0 383a20 387840 387590 385860 37ae80 37ad10 378260 3867c0 378da0 387980 37b5e0 386010 36eaa0 36bc90 39dcb0 3a8180 3aa760 3adf20 36b020 36ae40 3ad770 3ad250 3aac30 3ac870 3ac7f0 3ab0c0 3ac500 3aa9c0 3aa530 3aa360 3ab4b0 3ab350 3aae30 3adc00 3aa180 389330 3a7790 36aa80 3ad620 3ad070 3aaa40 3ac590 3ac620 36c860 36b280 36bbe0 3694d0 3977a0 3977d0 36b800 36b650 3ac3b0 3ac400 36ac20 3ad190 3abb50 3abc30 3ab9e0 > out/closure.txt
python3 -I scripts/closure.py 44e160 397250 397710 398a70 37a5a0 37a430 3ad360 > /dev/null
mkdir -p out/model
python3 -I scripts/helpers.py out/model 12000                                    # Task 3
for f in h-mul-drop-carry h-mul-high-limb-dropped; do python3 -I scripts/helpers.py out/model 2000 $f; done
python3 -I scripts/realarith.py out/model 2000 > out/model/realarith.log         # Tasks 1, 2, 5: MUL DIV MOD MULMOD
for f in gen1-not-spilled-before-call avx-not-spilled-before-udiv helper-args-swapped result-slot-wrong arg-slot-wrong free-offset-stale deferred-comparison-not-negated high-limb-dropped-in-mul-helper; do
  python3 -I scripts/realarith.py out/model 200 $f > out/model/realarith-$f.log; done
TASK4=1 python3 -I scripts/realarith.py out/model 2000 > out/model/realother.log  # Task 4
KINDS=SGT,SLT TASK4=1 python3 -I scripts/realarith.py out/model 2000 > out/model/realother-SGT_SLT.log
TASK4=1 python3 -I scripts/realarith.py out/model 50 discharge-setcc-wrong-flag > out/model/realother-discharge-setcc-wrong-flag.log
python3 -I scripts/task2.py out/model/realarith.json out/model/task2.json
python3 -I scripts/coverage.py out/model/coverage.json
