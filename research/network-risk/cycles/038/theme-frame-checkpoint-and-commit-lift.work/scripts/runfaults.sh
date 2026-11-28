#!/bin/bash
# each planted fault on 300 random sequences plus the named ones (seed 38500), family F, stops at the first catch
W=/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work
for f in revert_keeps_logs revert_keeps_third_list revert_forward_order commit_keeps_depth checkpoint_no_depth_raise; do
  for p in celo xlayer arc; do python3 -I $W/c37celo/scripts/jrun.py $p F 300 38500 $W/out/fault-$p-F-$f.json $f > $W/out/fault-$p-F-$f.log 2>&1 & done
  python3 -I $W/c37op/scripts/jrun.py opreth F 300 38500 $W/out/fault-opreth-F-$f.json $f > $W/out/fault-opreth-F-$f.log 2>&1 &
  wait
done
