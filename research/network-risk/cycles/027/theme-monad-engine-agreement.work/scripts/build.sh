#!/bin/bash
# Builds the fixed harness (src/harness_fixed.cpp) at one Monad tag, compiling only the harness and linking the
# Monad VM objects that cycle 23 compiled from the tagged source (cycles/023/theme-monad-compiled-coverage.work/build/VER-plain).
# Usage: scripts/build.sh VER   (0.16.5 | 0.16.7). Output build/VER/hxf
W=$(cd "$(dirname "$0")/.." && pwd); C23=$W/../../023/theme-monad-compiled-coverage.work
VER=$1
case $VER in 0.16.7) EVMC=dl/evmc-f6b7c57e; STUBV=src/stub167; HXD="";; 0.16.5) EVMC=dl/evmc-34795f4e; STUBV=src/stub165; HXD="-DHX_STACK_T=uint8_t";; *) echo bad; exit 1;; esac
cd $C23
INC="-Idl/third -Isrc/stub -I$STUBV -Idl/monad-$VER -Idl/asmjit/src -I$EVMC/include -Idl/openssl -Isrc"
OUT=$W/build/$VER; mkdir -p $OUT; P=build/$VER-plain
clang++ -std=c++23 -O2 -g -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE -march=haswell -Wno-switch $INC $HXD -c $W/src/harness_fixed.cpp -o $OUT/harness_fixed.o || exit 1
clang++ -o $OUT/hxf $OUT/harness_fixed.o $(ls $P/*.cpp.o | grep -v 'harness\|replay') $P/*.S.o $P/*.c.o $P/stub_bt.o $P/support16.o $P/covstub.o build/asmjit/*.o -lpthread || exit 1
ls -la $OUT/hxf; sha256sum $OUT/hxf
