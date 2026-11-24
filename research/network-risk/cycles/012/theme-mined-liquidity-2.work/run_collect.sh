cd /home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work
python3 collect.py 137 10000 300 300 raw/mod-137.json 2 > raw/collect-137.log 2>&1 &
python3 collect.py 56 1000 3000 300 raw/mod-56.json 4 > raw/collect-56.log 2>&1 &
python3 collect.py 4663 1000 3000 300 raw/mod-4663.json 4 > raw/collect-4663.log 2>&1 &
python3 collect.py 99901 10000 300 300 raw/mod-99901.json 2 > raw/collect-99901.log 2>&1 &
python3 collect.py 43114 10000 600 300 raw/mod-43114.json 2 > raw/collect-43114.log 2>&1 &
wait
