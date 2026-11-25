#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "queue.sh" > /dev/null; do sleep 5; done
W15=../../015/theme-monad-emitter-blocks.work
( ls $W15/runs/scen-1[0-3]?.txt; ls $W15/mass/mass-*.txt ) | xargs -P 4 -I{} sh -c 'b=$(basename {} .txt); HX_OPND_OUT=opnd/$b.txt ./hxop world.txt {} > opnd/$b.out 2>&1'
