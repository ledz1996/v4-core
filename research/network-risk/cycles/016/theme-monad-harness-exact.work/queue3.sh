#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "queue2.sh" > /dev/null; do sleep 5; done
W15=../../015/theme-monad-emitter-blocks.work; mkdir -p out-v167-512
( ls $W15/runs/scen-10?.txt; ls $W15/mass/mass-*-11.txt ) | xargs -P 4 -I{} sh -c "b=\$(basename {} .txt); HX_DIGEST=1 ./hx512 world.txt {} > out-v167-512/\$b.out 2>&1"
./runmined.sh rp512 mined/out-v167-512
./hx512 micro/world.txt micro/scen.txt > micro/out-v167-512.txt
