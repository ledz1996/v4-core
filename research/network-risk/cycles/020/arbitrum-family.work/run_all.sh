#!/bin/bash
# Cycle 18 reruns of the opdiff scripts for chain ids 42161 4663 99901, with client versions recorded around each.
cd /home/user/v4-core/research/network-risk
W=cycles/020/arbitrum-family.work
cv() { for u in https://arb1.arbitrum.io/rpc https://rpc.mainnet.chain.robinhood.com https://rpc.elysium.kinetiq.xyz; do echo "$(date -u +%FT%TZ) $1 $u $(bash $W/rpc.sh $u web3_clientVersion '[]')"; done >> $W/raw/clientVersions.log; }
T=tools/opdiff
cv before-battery;  python3 $T/battery.py  $W/raw/battery.json  42161 4663 99901 > $W/raw/battery.log 2>&1
cv before-targeted; python3 $T/targeted.py $W/raw/targeted.json 42161 4663 99901 > $W/raw/targeted.log 2>&1
cv before-pmdiff;   python3 $T/pmdiff.py   $W/raw/pmdiff.json 250 42161 4663 99901 > $W/raw/pmdiff.log 2>&1
cv before-pmdiff2;  python3 $T/pmdiff2.py  $W/raw/pmdiff2.json 300 42161 4663 99901 > $W/raw/pmdiff2.log 2>&1
cv before-swaps;    python3 $T/swaps.py    $W/raw/swaps.json 42161 4663 99901 > $W/raw/swaps.log 2>&1
cv before-replay;   python3 $T/replay.py   $W/raw/swaps.json $W/raw/replay.json 42161 4663 99901 > $W/raw/replay.log 2>&1
cv before-callsem; python3 $T/callsem.py $W/raw/callsem.json 42161 4663 99901 > $W/raw/callsem.log 2>&1
cv after-all
echo DONE >> $W/raw/clientVersions.log
python3 cycles/020/arbitrum-family.work/scripts/precscan.py cycles/020/arbitrum-family.work/raw/precscan.json > cycles/020/arbitrum-family.work/raw/precscan.log 2>&1
echo ALLDONE >> cycles/020/arbitrum-family.work/raw/clientVersions.log
