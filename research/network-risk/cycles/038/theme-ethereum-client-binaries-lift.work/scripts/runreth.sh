#!/bin/bash
# cycle 38: reth v2.11.0 handlers (rarith.py) on every set of out/reth/jobs.txt, both families
cd "$(dirname "$0")/.."
xargs -P ${PAR:-1} -L 1 bash -c 'python3 -I scripts/rarith.py $0 out/reth/$0.json >> out/reth/progress.log 2>&1 || echo "FAILED $0" >> out/reth/progress.log' < out/reth/jobs.txt
echo ALLDONE >> out/reth/progress.log
