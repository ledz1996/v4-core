cd /home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work
for c in 137 56 4663 99901 43114; do
  python3 analyze2.py $c raw/mod-$c.json raw/an2-$c.json 400 4 > raw/an2-$c.log 2>&1 &
done
wait
