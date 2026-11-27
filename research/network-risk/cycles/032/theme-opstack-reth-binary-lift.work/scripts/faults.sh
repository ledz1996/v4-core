#!/bin/sh
# planted fault runs; each stops after 20 differences
cd "$(dirname "$0")/.."
while pgrep -f "arith.py build/base-arm64.cfg.json out/arith-base-arm64" >/dev/null; do sleep 20; done
for spec in opreth-amd64:add_carry opreth-amd64:shl_bound opreth-amd64:mulmod_carry opreth-arm64:add_carry opreth-arm64:shl_bound base-arm64:add_carry base-amd64:add_carry; do
  n=${spec%%:*}; f=${spec#*:}
  python3 -I scripts/arith.py build/$n.cfg.json out/fault-arith-$n-$f.json all $f 0 7 > out/fault-arith-$n-$f.log 2>&1 &
done
for spec in opreth-amd64:push_lo opreth-amd64:jumpdest_byte base-amd64:push_lo opreth-arm64:push_lo base-arm64:push_lo; do
  n=${spec%%:*}; f=${spec#*:}
  NPREFIX=5 NRAND=50 python3 -I scripts/jd.py build/$n.jd.json out/fault-jd-$n-$f.json $f > out/fault-jd-$n-$f.log 2>&1
done
wait
for n in opreth-amd64 base-amd64 opreth-arm64 base-arm64; do python3 -I scripts/jd.py build/$n.jd.json out/jd-$n.json > out/jd-$n.log 2>&1; done
