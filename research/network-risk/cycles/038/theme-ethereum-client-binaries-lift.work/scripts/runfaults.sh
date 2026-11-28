#!/bin/bash
# cycle 38 Task 5: planted faults in the out-of-line handlers (drive.py + faults.py) and in geth's generated loop (gdrive.py + gfaults.py)
cd "$(dirname "$0")/.."
while ! grep -q ALLDONE out/runs/progress.log; do sleep 30; done
for t in geth-amd64 erigon-amd64 geth-arm64; do for f in carry limb shift cmpskip; do
  [ "$f" = cmpskip ] && [ "$t" = geth-arm64 ] && continue
  S=random; [ "$f" = shift ] && S=provevec; python3 -I scripts/drive.py $t $S 0 1 out/faults/$t-$f.json $f >> out/faults/progress.log 2>&1 || echo "FAILED $t $f" >> out/faults/progress.log
done; done
for f in carry limb borrow; do python3 -I scripts/gdrive.py random 0 10 out/faults/loop-$f.json $f >> out/faults/progress.log 2>&1 || echo "FAILED loop $f" >> out/faults/progress.log; done
echo ALLDONE >> out/faults/progress.log
