#!/bin/sh
cd /home/user/v4-core/research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work
python3 -I scripts/stnitro.py amd64 5000 out/st/nitro-amd64.json > out/st/nitro-amd64.log 2>&1
python3 -I scripts/stnitro.py arm64 2000 out/st/nitro-arm64.json > out/st/nitro-arm64.log 2>&1
python3 -I scripts/stnitro.py bal-amd64 1000 out/st/nitro-bal-amd64.json > out/st/nitro-bal-amd64.log 2>&1
echo NITRODONE
