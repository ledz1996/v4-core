#!/bin/bash
# seeds: full run 2026112838; fault runs 2026112839
cd /home/user/v4-core/research/network-risk/cycles/038/theme-tempo-credit-region-lift.work
B=/home/user/v4-core/research/network-risk/cycles/035/stablecoin-l1.work/dl/x_x86_64/tempo-v1.19.2-x86_64-unknown-linux-gnu
NT2=1500 python3 -I scripts/credit_region.py $B ../../036/theme-tempo-v1192-storage-lift.work/build build results/credit_none.json none 2026112838 40000 > results/credit_none.log 2>&1 &
for f in cross_from_original cross_from_new mint_wraps cold_credit_free budget_kept preserve_as_direct refund_pending_kept original_from_current credit_no_journal clean_update_free; do
  echo $f
done | xargs -P 3 -I{} sh -c 'NT2=300 SWEEPSTEP=10 python3 -I scripts/credit_region.py '$B' ../../036/theme-tempo-v1192-storage-lift.work/build build results/credit_fault_{}.json {} 2026112839 3000 > results/credit_fault_{}.log 2>&1'
wait
