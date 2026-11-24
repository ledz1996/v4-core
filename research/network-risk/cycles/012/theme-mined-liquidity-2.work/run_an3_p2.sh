cd /home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work
S=../../011/theme-mined-liquidity.work/raw
python3 analyze3.py 143 raw/an3-143.json 2000 4 $S/mod-143.json $S/mod-143b.json > raw/an3-143.log 2>&1 &
python3 analyze3.py 4326 raw/an3-4326.json 2000 4 $S/mod-4326.json > raw/an3-4326.log 2>&1 &
python3 analyze3.py 5042 raw/an3-5042.json 2000 4 $S/mod-5042.json > raw/an3-5042.log 2>&1 &
wait
