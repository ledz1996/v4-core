#!/bin/bash
# cycle 38, L-1306: rest of the cycle 36 Celo window, replayed from parent-block storage with cycles/024 gdrive.py (unchanged); second receipt endpoint rpc.ankr.com/celo
cd /home/user/v4-core/research/network-risk/cycles/038/op-stack-custom-gas.work
export RCPT_URLS="https://rpc.ankr.com/celo"
for i in 0 1 2 3 4 5 6 7; do timeout 3000 python3 -I /home/user/v4-core/research/network-risk/cycles/024/theme-replay-eleven.work/scripts/gdrive.py 42220 https://forno.celo.org replay/lwindow-rest.json $i 8 replay/lazy_$i.jsonl celo > replay/lazy_$i.log 2>&1 & done
wait; echo done > replay/done
