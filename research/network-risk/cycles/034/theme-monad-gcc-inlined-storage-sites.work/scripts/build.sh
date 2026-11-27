#!/bin/bash
# Cycle 34 Task 4: compile the extended hook (src/x86_hook.cpp from scripts/mkhook.py) with the cycle 31 clang flags and
# link it against the cycle 31 clang build's monad objects and the cycle 30 asmjit objects (read only, not rebuilt).
W=$(cd "$(dirname "$0")/.." && pwd)
C31=$(cd $W/../../031/theme-monad-gcc-real-states.work && pwd)
C23=$(cd $W/../../023/theme-monad-compiled-coverage.work && pwd)
AJ=$(cd $W/../../030/theme-monad-mined-native-coverage.work/build/asmjit && pwd)
VER=0.16.7; EVMC=dl/evmc-f6b7c57e; STUBV=src/stub167
OUT=$W/build/clang; mkdir -p $OUT
cd $C23
ARCH=-march=haswell
INC="-Idl/third -Isrc/stub -I$STUBV -Idl/monad-$VER -Idl/asmjit/src -I$EVMC/include -Idl/openssl"
clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $W/src/x86_hook.cpp -o $OUT/x86_hook.o || exit 1
B=$C31/build/clang
clang++ -std=c++23 -O2 $ARCH -o $OUT/asmdump_hook34 $B/asmdump.o $OUT/x86_hook.o $B/vm/*.o $B/stub_bt.o $B/support16.o $AJ/*.o -lpthread || exit 1
sha256sum $OUT/asmdump_hook34
