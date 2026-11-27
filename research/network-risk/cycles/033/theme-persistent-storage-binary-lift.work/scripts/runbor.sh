#!/bin/sh
# cycle 33: persistent storage runs of the bor v2.11.2 binaries (seed 32_1226_02, stgo.py's generator)
cd /home/user/v4-core/research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work
for t in bor-amd64 bormv-amd64 borpar-amd64; do python3 -I scripts/stgo2.py $t 5000 out/st/$t.json > out/st/$t.log 2>&1 & done
wait
for t in bor-arm64 bormv-arm64 borpar-arm64; do python3 -I scripts/stgo2.py $t 2000 out/st/$t.json > out/st/$t.log 2>&1 & done
wait
echo BORDONE
