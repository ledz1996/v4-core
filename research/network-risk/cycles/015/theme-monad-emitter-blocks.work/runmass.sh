#!/bin/bash
# per-path batteries: 50 scenarios x 2000 calls per path, interpreter vs native, with coverage
cd "$(dirname "$0")"
for p in approve transferFrom burn clear donate fallback big1 take swap; do
  for s in 1 2 3 4 5; do python3 gen_mass.py $p $((s+10)) 10 2000; mv mass-$p-$((s+10)).txt mass/; done
done
ls mass/mass-*.txt | xargs -P 4 -I{} sh -c 'b=$(basename {} .txt); HX_COV_OUT=mass/$b.cov ./hxcov world.txt {} > mass/$b.out 2>mass/$b.err'
for p in approve transferFrom burn clear donate fallback big1 take swap; do
  grep -h scenarios= mass/mass-$p-*.out | awk -F'[ =]' -v p=$p '{s+=$2; m+=$4} END {print p, "scenarios", s, "mismatches", m}'
done > mass/summary.txt
