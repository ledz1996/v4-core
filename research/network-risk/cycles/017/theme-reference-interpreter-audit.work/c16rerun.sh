#!/bin/sh
# Task 2: the 31 whole-transaction reruns of cycle 16 again, with pyevm_tx17.py (replay17.py)
python3 -c "
import json
for c,u,h,*_ in json.load(open('out/c16jobs.json')): print(c,u,h)
" | while read c u h; do
  [ -s out/c16-$c-$h.json ] || timeout 900 python3 replay17.py $c $u $h out/c16-$c-$h.json > /dev/null 2>> out/c16rerun.err
done
