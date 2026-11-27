#!/bin/sh
W=/home/user/v4-core/research/network-risk/cycles/035/theme-reth-keccak-asm-image-lift.work
B=$W/dl/rethbsc-v0.1.4/x/usr/local/bin/reth-bsc
A=$W/build/bsc/bsc_keccak.s
export KMODEL=bsc
python3 -I $W/scripts/run_all.py $W/scripts $B $A $W/out/bsc_full_none.json none > $W/out/bsc_full_none.log 2>&1 &
(for f in iota rot pad; do python3 -I $W/scripts/run_all.py $W/scripts $B $A $W/out/bsc_quick_$f.json $f quick > $W/out/bsc_quick_$f.log 2>&1; done) &
(for f in padc bcmp8 lenchk; do python3 -I $W/scripts/run_all.py $W/scripts $B $A $W/out/bsc_quick_$f.json $f quick > $W/out/bsc_quick_$f.log 2>&1; done) &
wait
echo done > $W/out/bsc.done
