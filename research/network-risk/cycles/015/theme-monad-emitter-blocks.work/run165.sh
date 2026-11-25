#!/bin/bash
# v0.16.5 build (interpreter vs native) on the per-path batteries and 10 of the 40 scenario files; faults on one file per path
cd "$(dirname "$0")"
( ls mass/mass-*.txt; ls runs/scen-1[0-0]?.txt ) | xargs -P 4 -I{} sh -c 'b=$(basename {} .txt); ./hx165 world.txt {} > v165/$b.out 2>v165/$b.err'
for f in f1 f2; do ls mass/mass-*-11.txt | xargs -P 4 -I{} sh -c "b=\$(basename {} .txt); ./hx_$f world.txt {} > fault/mass/\$b.$f.out 2>&1"; done
grep -h scenarios= v165/*.out | awk -F'[ =]' '{s+=$2; m+=$4} END {print "v0.16.5 scenarios", s, "mismatches", m}' > v165/summary.txt
for f in f1 f2; do for x in fault/mass/*.$f.out; do echo "$f $(basename $x) $(tail -1 $x)"; done; done > fault/summary.txt
