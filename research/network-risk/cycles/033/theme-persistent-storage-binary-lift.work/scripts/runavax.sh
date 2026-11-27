#!/bin/sh
cd /home/user/v4-core/research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work
python3 -I scripts/stgo2.py avax-amd64 5000 out/st/avax-amd64.json > out/st/avax-amd64.log 2>&1
python3 -I scripts/stgo2.py avax-arm64 2000 out/st/avax-arm64.json > out/st/avax-arm64.log 2>&1
echo AVAXDONE
