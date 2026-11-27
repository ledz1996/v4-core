#!/bin/bash
# runs every line of out/runs/jobs.txt (arch set shard nshard) through drive.py, four at a time (cycle 31: first field is the target)
cd "$(dirname "$0")/.."
xargs -P 4 -L 1 bash -c 'python3 -I scripts/drive.py $0 $1 $2 $3 out/runs/$0-$1-$2.json >> out/runs/progress.log 2>&1 || echo "FAILED $0 $1 $2" >> out/runs/progress.log' < ${JOBS:-out/runs/jobs.txt}
echo ALLDONE >> out/runs/progress.log
