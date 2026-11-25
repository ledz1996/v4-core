#!/bin/bash
# runs every input file on both releases: counters only (whole-run comparison), then counters plus the
# capture of one site at a time
cd "$(dirname "$0")/.."
W16=../../016/theme-monad-harness-exact.work
S=22378,22639,15519,16642,12232
mkdir -p out
run() { # name world scen cap
  for v in 167 165; do
    HX_COUNT_PCS=$S ./build/bin/hx$v $2 $3 > out/$1-$v-cnt.out 2> out/$1-$v-cnt.err
    HX_COUNT_PCS=$S HX_CAP_PCS=$4 HX_PRE_OUT=out/$1-$v.pre ./build/bin/hx$v $2 $3 > out/$1-$v-cap.out 2> out/$1-$v-cap.err
  done
}
run q128 runs/world-prologue.txt runs/prol-q128.txt 22378 &
run q96 runs/world-prologue.txt runs/prol-q96.txt 22639 &
run sar runs/world-prologue.txt runs/prol-sar.txt 15519 &
run shl runs/world-prologue.txt runs/prol-shl.txt 16642 &
wait
run cdl $W16/world.txt runs/cdl.txt 12232 &
run hook runs/world-hook.txt runs/hook.txt 15519 &
run pmq96 $W16/world.txt runs/pm-q96.txt 22639 &
run pmq128 $W16/world.txt runs/pm-q128.txt 22378 &
wait
for f in out/*.out; do echo "$f $(grep scenarios= $f)"; done
