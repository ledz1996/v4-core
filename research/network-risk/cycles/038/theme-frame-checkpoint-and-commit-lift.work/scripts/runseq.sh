#!/bin/bash
# runseq.sh: family F (frame code checkpoint, commit, revert) on 2,100 random sequences plus the named ones per binary
W=/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work
python3 -I $W/c37celo/scripts/jrun.py celo F 2100 38101 $W/out/seq-celo-F-38101.json none > $W/out/seq-celo-F-38101.log 2>&1 &
python3 -I $W/c37celo/scripts/jrun.py xlayer F 2100 38102 $W/out/seq-xlayer-F-38102.json none > $W/out/seq-xlayer-F-38102.log 2>&1 &
python3 -I $W/c37celo/scripts/jrun.py arc F 2100 38103 $W/out/seq-arc-F-38103.json none > $W/out/seq-arc-F-38103.log 2>&1 &
python3 -I $W/c37op/scripts/jrun.py opreth F 2100 38104 $W/out/seq-opreth-F-38104.json none > $W/out/seq-opreth-F-38104.log 2>&1 &
wait
