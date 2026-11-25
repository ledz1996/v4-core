#!/bin/bash
# 40 seeds x 500 scenarios through hxcov (interpreter vs native, with coverage)
cd "$(dirname "$0")"
for s in $(seq 100 139); do python3 gen.py $s 500 monad-pm-runtime.hex >/dev/null; mv scen-$s.txt runs/; done
ls runs/scen-*.txt | xargs -P 4 -I{} sh -c 'b=$(basename {} .txt); HX_COV_OUT=runs/$b.cov ./hxcov world.txt {} > runs/$b.out 2>runs/$b.err'
grep -h scenarios= runs/*.out | awk -F'[ =]' '{s+=$2; m+=$4} END {print "scenarios", s, "mismatches", m}' > runs/summary.txt
