#!/bin/bash
# Task 1 runs: sets 1, 2 and 6 at the real PoolManager address of each network, plus the fresh-address runs on Ethereum.
cd "$(dirname "$0")/.."
run_chain() {
  c=$1; t=$2
  for s in 1 2 6; do
    [ -f raw/runs/s$s-real-$c.json.gz ] || python3 scripts/realrun.py $s real $c raw/runs/s$s-real-$c.json.gz $t >> raw/runs/log-$c.txt 2>&1
  done
}
for c in 1 10 8453 130 7777777 480 57073 1868 42220 196 42161 137 56 143 4326 4217 5042; do run_chain $c 4 & done
for c in 4663 99901 43114 999; do run_chain $c 2 & done
( for s in 2 6; do [ -f raw/runs/s$s-fresh-1.json.gz ] || python3 scripts/realrun.py $s fresh 1 raw/runs/s$s-fresh-1.json.gz 4 >> raw/runs/log-fresh.txt 2>&1; done ) &
wait
echo ALLDONE >> raw/runs/log-fresh.txt
