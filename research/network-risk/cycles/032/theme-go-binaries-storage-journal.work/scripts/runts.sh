#!/bin/sh
# task 1 runs: 20,000 generated sequences (+8 fixed) per amd64 model, 5,000 (+8) per arm64 model, seed 31_1211_01
cd /home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work
mkdir -p out/ts
for t in bsc bor bor-par avax; do python3 -I scripts/tsgo.py $t-amd64 20000 out/ts/$t-amd64.json > out/ts/$t-amd64.log 2>&1 & done
wait
for t in bsc bor bor-par avax; do python3 -I scripts/tsgo.py $t-arm64 5000 out/ts/$t-arm64.json > out/ts/$t-arm64.log 2>&1 & done
wait
