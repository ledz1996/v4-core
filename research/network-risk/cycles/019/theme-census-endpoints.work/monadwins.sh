# Monad synced currency census, step 1: transaction lists for 20 windows of 2,000 blocks placed evenly from the
# PoolManager's deployment (29,255,895, eth_getCode bisection in raw/gap/143.json) to head, with the cycle 18 logscan.py.
L=../../018/theme-sync-leak-census.work/logscan.py
DEP=29255895; HEAD=$1
for k in $(seq 0 19); do
  A=$(( DEP + (HEAD - DEP - 2000) * k / 19 )); B=$(( A + 1999 ))
  [ -s raw/m143/logs-$k.json ] && continue
  python3 $L 0x188d586ddcf52439676ca21a244753fa19f9ea8e $A $B 100 raw/m143/logs-$k.json 3 https://rpc1.monad.xyz https://rpc4.monad.xyz https://rpc-mainnet.monadinfra.com >> raw/m143/logs.log 2>&1
  echo "$k $A $B $(date -u +%T)" >> raw/m143/logs.log
done
echo ALLDONE >> raw/m143/logs.log
