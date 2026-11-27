#!/bin/bash
# runfaults.sh <profile> <family> <spec> <fault>... : each planted fault on 300 random sequences plus the named ones (seed 37500)
W=/home/user/v4-core/research/network-risk/cycles/037/theme-celo-xlayer-arc-journal-lift.work
P=$1; F=$2; S=$3; shift 3
for f in "$@"; do python3 -I $W/scripts/jrun.py $P $F 300 37500 $W/out/fault-$P-$F-$f.json $f $S > $W/out/fault-$P-$F-$f.log 2>&1; done
