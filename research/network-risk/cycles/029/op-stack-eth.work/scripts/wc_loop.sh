#!/bin/bash
# World Chain: thirdweb's public endpoint rate limits, so run one scenario per process with long pauses
cd /home/user/v4-core/research/network-risk/cycles/029/op-stack-eth.work
python3 -c "
import sys; sys.path.insert(0,'/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts')
import scen28 as X; print('\n'.join(X.SCEN))" > out/scen-names.txt
i=0
while IFS= read -r n; do
  for t in 1 2 3 4 5; do
    python3 scripts/scen_rpc.py out/wc/scen-480-$i.json https://480.rpc.thirdweb.com "$n" > out/wc/scen-480-$i.log 2>&1
    grep -q "diffs" out/wc/scen-480-$i.log && break; sleep 250
  done
  i=$((i+1)); sleep 45
done < out/scen-names.txt
echo done > out/wc/ALLDONE
