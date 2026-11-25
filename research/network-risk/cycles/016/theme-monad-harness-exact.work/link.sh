#!/bin/bash
# link harness against an object directory: ./link.sh OUTDIR binary [extra flags]
cd "$(dirname "$0")"
OUT=$1; BIN=$2; shift 2; MONAD=${MONAD:-dl/monad}; EVMC=${EVMC:-dl/evmc}; ARCH=${ARCH:--march=haswell}; SRC=${SRC:-harness.cpp}
INC="-Idl/third -Istub -I${STUBV:-stub167} -I$MONAD -Idl/asmjit/src -I$EVMC/include"
clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC "$@" -c $SRC -o $OUT/$(basename $SRC .cpp).main.o || exit 1
clang++ -std=c++23 -O2 $ARCH $INC -c stub_bt.cpp -o $OUT/stub_bt.o || exit 1
gcc -O2 -c support16.c -o $OUT/support16.o
clang++ -o $BIN $OUT/$(basename $SRC .cpp).main.o $OUT/*.cpp.o $OUT/*.S.o $OUT/*.c.o $OUT/stub_bt.o $OUT/support16.o $OUT/asmjit/*.o -lpthread
