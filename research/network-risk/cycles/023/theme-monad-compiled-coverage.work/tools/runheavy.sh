#!/bin/bash
# ./tools/runheavy.sh BUILD OUTDIR : the 16 full-range scripts whose call trees cycle 18 took from Monad's node (trees-monadnode.txt),
# with the gas each PoolManager frame had on the node
cd "$(dirname "$0")/.."
B=$1; OD=$2; mkdir -p $OD
HX_PM=00000000000000000000000000000000504d0001 HX_COVTMP=$OD HX_COVOUT=$OD/heavy18.cov ./build/$B/rp sets/s3/pm-build-at-504d0001.hex sets/heavy18/heavy18.txt > $OD/heavy18.out 2> $OD/heavy18.err
