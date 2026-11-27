#!/bin/sh
# planted fault runs, 300 sequences each, after the main runs
cd /home/user/v4-core/research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work
for t in nitro bor borpar avax; do python3 -I scripts/plant2.py $t 300 out/faults > out/faults-$t.log 2>&1 & done
wait
echo FAULTSDONE
