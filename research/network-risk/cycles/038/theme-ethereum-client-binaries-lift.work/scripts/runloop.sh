#!/bin/bash
# cycle 38: every line of out/loop/jobs.txt (set shard nshard) through gdrive.py (geth v1.17.10 execUntraced)
cd "$(dirname "$0")/.."
xargs -P ${PAR:-1} -L 1 bash -c 'python3 -I scripts/gdrive.py $0 $1 $2 out/loop/$0-$1.json >> out/loop/progress.log 2>&1 || echo "FAILED $0 $1" >> out/loop/progress.log' < out/loop/jobs.txt
echo ALLDONE >> out/loop/progress.log
