#!/bin/bash
# ./tools/runscen.sh BUILD OUTDIR : the cycle 15 scenario files (scen-100..139) and per-path batteries (mass-*), as cycle 16 ran them,
# with native coverage per file
cd "$(dirname "$0")/.."
B=$1; OD=$2; W15=../../015/theme-monad-emitter-blocks.work; mkdir -p $OD
( ls $W15/runs/scen-1[0-3]?.txt; ls $W15/mass/mass-*.txt ) | xargs -P ${P:-2} -I{} sh -c "b=\$(basename {} .txt); [ -f $OD/\$b.cov ] || HX_DIGEST=1 HX_COVTMP=$OD HX_COVOUT=$OD/\$b.cov ./build/$B/hx src/world.txt {} > $OD/\$b.out 2>$OD/\$b.err"
grep -h scenarios= $OD/*.out | awk -F'[ =]' '{s+=$2; m+=$4} END {print "scenarios", s, "mismatches", m}' > $OD/summary.txt
