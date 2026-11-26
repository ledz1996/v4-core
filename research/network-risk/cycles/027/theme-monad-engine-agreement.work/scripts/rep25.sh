#!/bin/bash
# Cycle 27: the cycle 25 harness effects (case 1369 in the 3,066-token world and alone, case 1528 six-scenario file once
# and three times) on the cycle 23 binaries (old) and the fixed binaries, both tags, MALLOC_PERTURB_ unset, 165 and 90.
# Output: out/rep25/<bin>-<ver>-<input>-mp<v>.txt (harness stdout with HX_DIGEST digests).
W=$(cd "$(dirname "$0")/.." && pwd); H=$W/../../025/theme-unexecuted-sides.work/out/hx; O=$W/out/rep25; mkdir -p $O
B23=$W/../../023/theme-monad-compiled-coverage.work/build
cat $H/c1528/s.txt $H/c1528/s.txt $H/c1528/s.txt > $O/s1528x3.txt
for ver in 0.16.5 0.16.7; do for b in old fixed; do
  [ $b = old ] && X=$B23/$ver-plain/hx || X=$W/build/$ver/hxf
  for mp in none 165 90; do
    E=""; [ $mp != none ] && E="MALLOC_PERTURB_=$mp"
    env $E HX_DIGEST=1 $X $H/world.txt $H/scen-1369.txt > $O/$b-$ver-1369big-mp$mp.txt
    env $E HX_DIGEST=1 $X $H/world-1369.txt $H/scen-1369.txt > $O/$b-$ver-1369small-mp$mp.txt
    env $E HX_DIGEST=1 $X $H/c1528/w.txt $H/c1528/s.txt > $O/$b-$ver-1528-mp$mp.txt
    env $E HX_DIGEST=1 $X $H/c1528/w.txt $O/s1528x3.txt > $O/$b-$ver-1528x3-mp$mp.txt
  done
done; done
