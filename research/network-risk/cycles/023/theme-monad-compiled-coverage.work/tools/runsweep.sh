#!/bin/bash
# ./tools/runsweep.sh BUILD OUTDIR : out-of-gas sweep (task 3). Every PoolManager frame of the listed transactions gets the same gas G,
# for G in each range below; interpreter and native code are compared on status, gas, output, storage, transient storage and logs.
cd "$(dirname "$0")/.."
B=$1; OD=$2; mkdir -p $OD; C16=../../016/theme-monad-harness-exact.work
P="HX_PM=00000000000000000000000000000000504d0001"
env HX_PM=00000000000000000000000000000000504d0001 HX_GAS_SWEEP=600:300000:7487 HX_COVTMP=$OD HX_COVOUT=$OD/sw-set3.cov ./build/$B/rp sets/s3/pm-build-at-504d0001.hex sets/s3/set3.txt > $OD/sw-set3.out 2> $OD/sw-set3.err &
env HX_PM=00000000000000000000000000000000504d0001 HX_GAS_SWEEP=800:300000:14983 HX_COVTMP=$OD HX_COVOUT=$OD/sw-set6.cov ./build/$B/rp sets/s3/pm-build-at-504d0001.hex sets/s6/set6.txt > $OD/sw-set6.out 2> $OD/sw-set6.err &
env HX_PM=00000000000000000000000000000000504d0001 HX_GAS_SWEEP=700:200000:9973 HX_COVTMP=$OD HX_COVOUT=$OD/sw-set2.cov ./build/$B/rp sets/s3/pm-build-at-504d0001.hex sets/s2/set2.txt > $OD/sw-set2.out 2> $OD/sw-set2.err &
env HX_GAS_SWEEP=900:300000:19997 HX_COVTMP=$OD HX_COVOUT=$OD/sw-mined0.cov ./build/$B/rp monad-pm-runtime.hex $C16/mined/part0.txt > $OD/sw-mined0.out 2> $OD/sw-mined0.err &
wait
