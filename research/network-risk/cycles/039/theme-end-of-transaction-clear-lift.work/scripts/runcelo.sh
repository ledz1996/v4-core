#!/bin/sh
# Cycle 39 Task 3: celo-reth JournalInner::finalize 0x1d66c80, 1,000 populated states (seed 39029) and five faults.
cd /home/user/v4-core/research/network-risk/cycles/039/theme-end-of-transaction-clear-lift.work
python3 -I scripts/txrun39.py celo1010 finalize 1d66c80 1000 39029 out/main-celo1010-1d66c80.json > out/main-celo1010-1d66c80.log 2>&1
for F in transient_kept journal_kept depth_kept txid_kept logs_kept; do python3 -I scripts/txrun39.py celo1010 finalize 1d66c80 40 39029 out/fault-celo1010-1d66c80-$F.json $F > out/fault-celo1010-1d66c80-$F.log 2>&1; done
