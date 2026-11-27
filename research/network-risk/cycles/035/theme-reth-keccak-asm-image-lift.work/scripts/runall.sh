#!/bin/sh
# runs the full set and the planted faults; outputs in out/
W=/home/user/v4-core/research/network-risk/cycles/035/theme-reth-keccak-asm-image-lift.work
B=$W/dl/xlayer-rc1/x/usr/local/bin/op-reth
A=$W/build/xl_keccak.s
python3 -I $W/scripts/run_all.py $W/scripts $B $A $W/out/full_none.json none > $W/out/full_none.log 2>&1 &
for f in iota rot pad padc bcmp8 lenchk; do
  python3 -I $W/scripts/run_all.py $W/scripts $B $A $W/out/quick_$f.json $f quick > $W/out/quick_$f.log 2>&1 &
done
wait
echo done > $W/out/all.done
