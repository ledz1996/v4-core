#!/bin/sh
# Cycle 39: main runs (500 populated states per routine, seeds 39001+index) and planted-fault runs (5 faults per
# routine, 40 states each, stop at first catch). Four at a time.
cd /home/user/v4-core/research/network-risk/cycles/039/theme-end-of-transaction-clear-lift.work
python3 -I -c "
import sys;sys.path.insert(0,'scripts');from units import UNITS
for i,(p,k,f) in enumerate(UNITS): print(p,k,'%x'%f,39001+i)" > out/units.txt
while read p k f s; do echo "python3 -I scripts/txrun39.py $p $k $f 500 $s out/main-$p-$f.json > out/main-$p-$f.log 2>&1"; done < out/units.txt > out/jobs.txt
while read p k f s; do for F in transient_kept journal_kept depth_kept txid_kept logs_kept; do echo "python3 -I scripts/txrun39.py $p $k $f 40 $s out/fault-$p-$f-$F.json $F > out/fault-$p-$f-$F.log 2>&1"; done; done < out/units.txt >> out/jobs.txt
xargs -P 4 -I CMD sh -c CMD < out/jobs.txt
