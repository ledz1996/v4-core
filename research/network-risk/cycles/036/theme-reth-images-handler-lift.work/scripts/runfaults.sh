#!/bin/bash
cd /home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work
for n in celo xlayer bsc bsch arc085 arc086; do
 echo "ONLY=MUL python3 -I scripts/arith.py build/$n.cfg.json out/fault-$n-mul_dropped_carry.json all mul_dropped_carry > out/fault-$n-mul_dropped_carry.log 2>&1"
 echo "ONLY=MULMOD python3 -I scripts/arith.py build/$n.cfg.json out/fault-$n-mulmod_wrong_limb.json all mulmod_wrong_limb > out/fault-$n-mulmod_wrong_limb.log 2>&1"
 echo "NPREFIX=5 NRAND=50 python3 -I scripts/jd.py build/$n.jd.json out/fault-$n-jumpdest_byte.json jumpdest_byte > out/fault-$n-jumpdest_byte.log 2>&1"
 echo "NPREFIX=5 NRAND=50 python3 -I scripts/jd.py build/$n.jd.json out/fault-$n-bitmap_bit.json bitmap_bit > out/fault-$n-bitmap_bit.log 2>&1"
done | xargs -P 2 -I{} bash -c '{}'
touch out/faults.done
