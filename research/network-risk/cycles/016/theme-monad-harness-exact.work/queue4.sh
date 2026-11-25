#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "queue3.sh" > /dev/null; do sleep 5; done
W15=../../015/theme-monad-emitter-blocks.work; mkdir -p fault/out-f5 fault/out-f3
ls $W15/mass/mass-*-11.txt $W15/runs/scen-10[0-3].txt | xargs -P 4 -I{} sh -c "b=\$(basename {} .txt); ./hx_f5 world.txt {} > fault/out-f5/\$b.out 2>&1; ./hx_f3 world.txt {} > fault/out-f3/\$b.out 2>&1"
python3 gasdiff.py mined/part0.txt mined/part1.txt mined/part2.txt mined/part3.txt > mined/gasdiff.json
