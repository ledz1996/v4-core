#!/bin/bash
# cycle 40, L-1306: last 57 transactions of the cycle 36 Celo window, plus the non-converged ones with a higher round limit; cycles/024 gdrive.py unchanged
cd /home/user/v4-core/research/network-risk/cycles/040/op-stack-custom-gas.work
export RCPT_URLS="https://rpc.ankr.com/celo"
G=/home/user/v4-core/research/network-risk/cycles/024/theme-replay-eleven.work/scripts/gdrive.py
for i in 0 1 2 3 4 5 6 7; do timeout 3000 python3 -I $G 42220 https://forno.celo.org replay/lwindow-left.json $i 8 replay/lazy_$i.jsonl celo > replay/lazy_$i.log 2>&1 & done
MAXR=250 timeout 3000 python3 -I $G 42220 https://forno.celo.org replay/lwindow-nc.json 0 1 replay/rerun_nc.jsonl celo > replay/rerun_nc.log 2>&1 &
wait; echo done > replay/done
