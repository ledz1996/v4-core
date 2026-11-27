#!/bin/sh
# after runts.sh: storage model (bsc), keccak cache model (bor), planted faults on every target
cd /home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work
mkdir -p out/st out/kk out/faults
python3 -I scripts/stgo.py bsc-amd64 5000 out/st/bsc-amd64.json > out/st/bsc-amd64.log 2>&1 &
python3 -I scripts/stgo.py bsc-arm64 2000 out/st/bsc-arm64.json > out/st/bsc-arm64.log 2>&1 &
python3 -I scripts/kk.py amd64 5000 out/kk/bor-amd64.json > out/kk/bor-amd64.log 2>&1 &
python3 -I scripts/kk.py arm64 2000 out/kk/bor-arm64.json > out/kk/bor-arm64.log 2>&1 &
wait
(for t in bsc-amd64 bor-amd64 bor-par-amd64 avax-amd64; do python3 -I scripts/plant.py ts $t 200 out/faults; done > out/faults/ts-amd64.log 2>&1) &
(for t in bsc-arm64 bor-arm64 bor-par-arm64 avax-arm64; do python3 -I scripts/plant.py ts $t 100 out/faults; done > out/faults/ts-arm64.log 2>&1) &
(python3 -I scripts/plant.py st amd64 200 out/faults; python3 -I scripts/plant.py st arm64 100 out/faults) > out/faults/st.log 2>&1 &
(for f in key_last8 store_zero_value; do python3 -I scripts/kk.py amd64 200 out/faults/kk-amd64-$f.json $f; python3 -I scripts/kk.py arm64 100 out/faults/kk-arm64-$f.json $f; done) > out/faults/kk.log 2>&1 &
wait
