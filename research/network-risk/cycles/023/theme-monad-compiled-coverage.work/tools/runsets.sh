#!/bin/bash
# ./tools/runsets.sh BUILD OUTDIR sets... : run tools/runset.sh for each set in parallel
cd "$(dirname "$0")/.."
B=$1; OD=$2; shift 2
for s in "$@"; do ./tools/runset.sh $B set$s sets/s$s/set$s.txt $OD & done; wait
