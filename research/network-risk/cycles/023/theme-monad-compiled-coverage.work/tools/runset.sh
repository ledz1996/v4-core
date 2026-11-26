#!/bin/bash
# ./tools/runset.sh BUILD NAME TXFILE OUTDIR : one replay-format file of script transactions (PoolManager at 0x...504d0001,
# the build of this checkout with that address as its immutable), interpreter vs native vs the reference tree, with coverage.
cd "$(dirname "$0")/.."
B=$1; N=$2; F=$3; OD=$4; mkdir -p $OD
HX_PM=00000000000000000000000000000000504d0001 HX_GAS=4000000000 HX_COVTMP=$OD HX_COVOUT=$OD/$N.cov ./build/$B/rp sets/s3/pm-build-at-504d0001.hex $F > $OD/$N.out 2> $OD/$N.err
