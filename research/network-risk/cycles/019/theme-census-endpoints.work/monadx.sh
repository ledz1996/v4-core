# Cross-check of the Monad census transaction lists: the same 20 windows scanned again on rpc.monad.xyz alone.
L=../../018/theme-sync-leak-census.work/logscan.py
python3 -c "import json;[print(w[1],w[2]) for w in json.load(open('raw/m143/txmeta.json'))['windows']]" | while read A B; do
  python3 $L 0x188d586ddcf52439676ca21a244753fa19f9ea8e $A $B 100 raw/m143x/logs-$A.json 2 https://rpc.monad.xyz >> raw/m143x/logs.log 2>&1
done
echo ALLDONE >> raw/m143x/logs.log
