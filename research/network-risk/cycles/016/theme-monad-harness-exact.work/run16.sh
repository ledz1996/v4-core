#!/bin/bash
# ./run16.sh BIN OUTDIR : the 40 x 500 scenario files and 45 per-path battery files of cycle 15, interpreter vs native, with digests
cd "$(dirname "$0")"
BIN=$1; OD=$2; W15=../../015/theme-monad-emitter-blocks.work; mkdir -p $OD
( ls $W15/runs/scen-1[0-3]?.txt; ls $W15/mass/mass-*.txt ) | xargs -P 4 -I{} sh -c "b=\$(basename {} .txt); HX_DIGEST=1 ./$BIN world.txt {} > $OD/\$b.out 2>$OD/\$b.err"
grep -h scenarios= $OD/scen-*.out | awk -F'[ =]' '{s+=$2; m+=$4} END {print "scenario files: scenarios", s, "mismatches", m}' > $OD/summary.txt
for p in approve transferFrom burn clear donate fallback big1 take swap; do
  grep -h scenarios= $OD/mass-$p-*.out | awk -F'[ =]' -v p=$p '{s+=$2; m+=$4} END {print p, "scenarios", s, "mismatches", m}'
done >> $OD/summary.txt
cat $OD/*.err | sort | uniq -c | sort -rn | head > $OD/errs.txt
