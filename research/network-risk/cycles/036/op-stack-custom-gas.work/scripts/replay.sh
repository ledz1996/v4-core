#!/bin/bash
# cycle 36, L-1067: Celo parent-storage replay of window transactions 2480 to 2879 (cycles/024 gdrive.py, unchanged)
cd /home/user/v4-core/research/network-risk/cycles/036/op-stack-custom-gas.work
for i in 0 1 2 3 4 5 6 7; do python3 -I /home/user/v4-core/research/network-risk/cycles/024/theme-replay-eleven.work/scripts/gdrive.py 42220 https://forno.celo.org replay/lwindow-2480.json $i 8 replay/lazy_$i.jsonl celo > replay/lazy_$i.log 2>&1 & done
wait; echo done > replay/done
