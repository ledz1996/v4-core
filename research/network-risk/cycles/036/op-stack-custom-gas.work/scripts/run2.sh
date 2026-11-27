#!/bin/bash
# cycle 36: arithmetic handler runs in the x86-64 model for the Celo and X Layer images
cd /home/user/v4-core/research/network-risk/cycles/036/op-stack-custom-gas.work
for i in 0 1 2; do python3 -I scripts/arith.py build/celo-a.cfg.json out/arith-celo-a-$i.json all none $i 3 > out/arith-celo-a-$i.log 2>&1 & done
wait
(ONLY=SIGNEXTEND python3 -I scripts/arith.py build/xl-a.cfg.json out/arith-xl-a-sx.json all > out/arith-xl-a-sx.log 2>&1) &
(for c in xl-b xl-c celo-b celo-c celo-d; do ONLY=EXP python3 -I scripts/arith.py build/$c.cfg.json out/arith-$c-exp.json all > out/arith-$c-exp.log 2>&1; done) &
wait
echo done > out/run2.done
