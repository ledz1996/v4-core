#!/bin/bash
# cycle 38 Task 3 for reth v2.11.0: every kernel on all programs, then the planted faults
cd "$(dirname "$0")/.."
for k in avx512 avx2 none; do python3 -I scripts/rjd.py dl/build/reth dl/reth/reth out/jd/reth-$k.json $k none >> out/jd/rprogress.log 2>&1; done
python3 -I scripts/rjd.py dl/build/reth dl/reth/reth out/jd/reth-avx2-fault-avx2_maxub.json avx2 avx2_maxub >> out/jd/rprogress.log 2>&1
python3 -I scripts/rjd.py dl/build/reth dl/reth/reth out/jd/reth-avx512-fault-avx512_perm.json avx512 avx512_perm >> out/jd/rprogress.log 2>&1
python3 -I scripts/rjd.py dl/build/reth dl/reth/reth out/jd/reth-none-fault-scalar_jumpdest.json none scalar_jumpdest >> out/jd/rprogress.log 2>&1
python3 -I scripts/rjd.py dl/build/reth dl/reth/reth out/jd/reth-none-fault-scalar_push.json none scalar_push >> out/jd/rprogress.log 2>&1
echo ALLDONE >> out/jd/rprogress.log
