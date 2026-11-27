#!/bin/bash
W=$(dirname $(dirname $(realpath $0)))
while [ ! -f $W/runs/pm911/exit.txt ]; do sleep 5; done
$W/scripts/runlist.sh pmnew $W/data/pm-new-blocks.txt
$W/scripts/runlist.sh newest20k $W/data/newest20k.txt
$W/scripts/runlist.sh pmrest $W/data/pmrest.txt
