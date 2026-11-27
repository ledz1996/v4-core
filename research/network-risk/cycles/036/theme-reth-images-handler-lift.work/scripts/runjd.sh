#!/bin/bash
cd /home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work
for n in celo xlayer bsc bsch arc085 arc086; do echo "python3 -I scripts/jd.py build/$n.jd.json out/jd-$n.json > out/jd-$n.log 2>&1"; done | xargs -P 3 -I{} bash -c '{}'
touch out/jd.done
