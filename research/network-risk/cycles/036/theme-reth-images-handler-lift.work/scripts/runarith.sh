#!/bin/bash
# full arithmetic runs, 4 shards per binary, then every EXP variant on the EXP vectors; 4 jobs at a time
W=/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work
cd $W
jobs=()
for n in celo xlayer bsc bsch arc085 arc086; do for s in 0 1 2 3; do jobs+=("python3 -I scripts/arith.py build/$n.cfg.json out/arith-$n-$s.json all none $s 4 > out/arith-$n-$s.log 2>&1"); done; done
for n in celo xlayer bsc bsch arc085 arc086; do
  for e in $(python3 -c "import json;print(' '.join(json.load(open('build/$n.cfg.json'))['expVariants']))"); do
    python3 -c "import json;c=json.load(open('build/$n.cfg.json'));c['exp_handler']='$e';json.dump(c,open('build/$n-exp-$e.cfg.json','w'),indent=1)"
    jobs+=("ONLY=EXP python3 -I scripts/arith.py build/$n-exp-$e.cfg.json out/arith-$n-exp-$e.json all > out/arith-$n-exp-$e.log 2>&1")
  done
done
printf '%s\n' "${jobs[@]}" | xargs -P 4 -I{} bash -c '{}'
touch out/arith.done
