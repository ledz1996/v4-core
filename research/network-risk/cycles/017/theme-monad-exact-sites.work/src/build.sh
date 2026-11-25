#!/bin/bash
# Instrumented harness on the exact dependencies of cycle 16: only x86.cpp (patched copy) and
# interpreter/execute.cpp (patched instruction_table.hpp) are recompiled; every other object is
# the cycle 16 object of that release. Usage: build.sh 167|165 [extra flags]
set -e
W=$(cd "$(dirname "$0")/.." && pwd); W16=$W/../../016/theme-monad-harness-exact.work
V=$1; shift
if [ $V = 167 ]; then MONAD=$W16/dl/monad; EVMC=$W16/dl/evmc; STUBV=$W16/stub167; OBJ=$W16/build/v167; else MONAD=$W16/dl/monad-0.16.5; EVMC=$W16/dl/evmc165; STUBV=$W16/stub165; OBJ=$W16/build/v165; fi
P=$W/build/p$V; O=$W/build/o$V; mkdir -p $O
INC="-I$P/inc -I$W16/dl/third -I$W16/stub -I$STUBV -I$MONAD -I$W16/dl/asmjit/src -I$EVMC/include"
FL="-std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE -march=haswell -Wno-switch"
clang++ $FL $INC -c $P/x86.cpp -o $O/x86.o &
clang++ $FL $INC -c $MONAD/category/vm/interpreter/execute.cpp -o $O/execute.o &
clang++ $FL $INC "$@" -c $W/src/harness_x.cpp -o $O/harness_x.o &
clang++ -std=c++23 -O2 -march=haswell $INC -c $W16/stub_bt.cpp -o $O/stub_bt.o &
gcc -O2 -c $W16/support16.c -o $O/support16.o &
wait
OBJS=$(ls $OBJ/*.cpp.o $OBJ/*.S.o $OBJ/*.c.o | grep -v -e compiler_ir_x86.cpp.o -e interpreter_execute.cpp.o)
clang++ -o $W/build/bin/hx$V $O/harness_x.o $O/x86.o $O/execute.o $OBJS $O/stub_bt.o $O/support16.o $OBJ/asmjit/*.o -lpthread
echo built $W/build/bin/hx$V
