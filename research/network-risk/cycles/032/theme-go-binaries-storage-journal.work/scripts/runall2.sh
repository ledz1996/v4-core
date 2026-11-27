#!/bin/sh
# rerun of the arm64 transient runs (first attempt killed by the memory limit), then runrest.sh
cd /home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work
for t in bsc bor bor-par avax; do python3 -I scripts/tsgo.py $t-arm64 5000 out/ts/$t-arm64.json > out/ts/$t-arm64.log 2>&1 & done
wait
scripts/runrest.sh
echo ALLDONE
