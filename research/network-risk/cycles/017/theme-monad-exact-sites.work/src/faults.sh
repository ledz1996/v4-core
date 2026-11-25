#!/bin/bash
# one planted fault at a time (HX_FAULT_PC), every input file, both releases; whole-run comparison (counters only)
# and site-level comparison (capture of the faulted site)
cd "$(dirname "$0")/.."
W16=../../016/theme-monad-harness-exact.work
S=22378,22639,15519,16642,12232
mkdir -p fault
for F in 22378 22639 15519 16642 12232; do
 for v in 167 165; do
  for t in "q128 runs/world-prologue.txt runs/prol-q128.txt" "q96 runs/world-prologue.txt runs/prol-q96.txt" "sar runs/world-prologue.txt runs/prol-sar.txt" "shl runs/world-prologue.txt runs/prol-shl.txt" "cdl $W16/world.txt runs/cdl.txt" "hook runs/world-hook.txt runs/hook.txt" "pmq96 $W16/world.txt runs/pm-q96.txt" "pmq128 $W16/world.txt runs/pm-q128.txt"; do
   set -- $t
   ( HX_FAULT_PC=$F HX_COUNT_PCS=$S ./build/bin/hx$v $2 $3 | grep scenarios= | sed "s/^/$F $v $1 whole /";
     HX_FAULT_PC=$F HX_COUNT_PCS=$S HX_CAP_PCS=$F ./build/bin/hx$v $2 $3 | grep scenarios= | sed "s/^/$F $v $1 site /" ) &
  done
  wait
 done
done > fault/summary.txt
cat fault/summary.txt
