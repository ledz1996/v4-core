#!/bin/bash
cd "$(dirname "$0")"
while pgrep -f "rp_f5 monad" > /dev/null; do sleep 5; done
./hx165 micro/world.txt micro/scen.txt > micro/out-v165.txt &
./runmined.sh rp165 mined/out-v165
wait
