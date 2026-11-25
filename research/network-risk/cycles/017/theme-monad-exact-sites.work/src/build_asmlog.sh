#!/bin/bash
set -e
W=$(cd "$(dirname "$0")/.." && pwd); W16=$W/../../016/theme-monad-harness-exact.work
V=$1
if [ $V = 167 ]; then MONAD=$W16/dl/monad; EVMC=$W16/dl/evmc; STUBV=$W16/stub167; OBJ=$W16/build/v167; else MONAD=$W16/dl/monad-0.16.5; EVMC=$W16/dl/evmc165; STUBV=$W16/stub165; OBJ=$W16/build/v165; fi
P=$W/build/p$V; O=$W/build/o$V
INC="-I$P/inc -I$W16/dl/third -I$W16/stub -I$STUBV -I$MONAD -I$W16/dl/asmjit/src -I$EVMC/include"
clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE -march=haswell -Wno-switch $INC -c $W/src/asmlog_x.cpp -o $O/asmlog_x.o
OBJS=$(ls $OBJ/*.cpp.o $OBJ/*.S.o $OBJ/*.c.o | grep -v -e compiler_ir_x86.cpp.o -e interpreter_execute.cpp.o)
clang++ -o $W/build/bin/asmlog$V $O/asmlog_x.o $O/x86.o $O/execute.o $OBJS $O/stub_bt.o $O/support16.o $OBJ/asmjit/*.o -lpthread
