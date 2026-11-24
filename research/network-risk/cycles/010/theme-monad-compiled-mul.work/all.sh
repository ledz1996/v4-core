#!/bin/sh
# Runs every path with four seeds of N/4 cases each, four processes at a time.
W=$(dirname "$0")
for p in mulmod96 mulmod128 tickconst mullit runtimemul mul192 muldiv mulmodall exp; do
  for s in 1 2 3 4; do python3 -I "$W/run.py" "$W" $p 250000 $s & done; wait
done
