#!/bin/bash
# Cycle 31 Task 1. Rebuild the clang harness emitter path of monad v0.16.7 from the source cycle 23 fetched
# (cycles/023/theme-monad-compiled-coverage.work/dl), same flags as cycles/030/theme-monad-mined-native-coverage.work/scripts/build.sh.
# Every monad object is compiled fresh into build/; the asmjit objects of cycle 30 (third-party, same flags) are linked.
# Produces build/asmdump_orig (x86.cpp unchanged) and build/asmdump_hook (src/x86_hook.cpp: state log hook only).
# With CXX=g++ it builds the same with the system gcc instead (build/gcc/...).
W=$(cd "$(dirname "$0")/.." && pwd)
C23=$(cd $W/../../023/theme-monad-compiled-coverage.work && pwd)
C27=$(cd $W/../../027/theme-monad-engine-agreement.work && pwd)
AJ=$(cd $W/../../030/theme-monad-mined-native-coverage.work/build/asmjit && pwd)
VER=0.16.7; EVMC=dl/evmc-f6b7c57e; STUBV=src/stub167
CXX=${CXX:-clang++}; CC=${CC:-clang}
case $CXX in g++) OUT=$W/build/gcc; CXXF="-std=c++23 -O2 -include $W/src/gcc13_shim.h";; *) OUT=$W/build/clang; CXXF="-std=c++23 -O2";; esac
cd $C23
mkdir -p $OUT/vm
ARCH=-march=haswell
INC="-Idl/third -Isrc/stub -I$STUBV -Idl/monad-$VER -Idl/asmjit/src -I$EVMC/include -Idl/openssl"
VM="category/core/monad_exception.cpp category/vm/compiler/ir/basic_blocks.cpp category/vm/compiler/ir/x86/emitter.cpp category/vm/compiler/ir/x86/virtual_stack.cpp category/vm/evm/access_status.cpp category/vm/evm/delegation.cpp category/vm/evm/message.cpp category/vm/evm/page_storage_status.cpp category/vm/evm/revision.cpp category/vm/evm/status_code.cpp category/vm/evm/storage_status.cpp category/vm/evm/tx_context.cpp category/vm/interpreter/entry.S category/vm/interpreter/execute.cpp category/vm/interpreter/instruction_stats.cpp category/vm/interpreter/intercode.cpp category/vm/runtime/allocator.cpp category/vm/runtime/call.cpp category/vm/runtime/context.S category/vm/runtime/context.cpp category/vm/runtime/create.cpp category/vm/runtime/data.cpp category/vm/runtime/environment.cpp category/vm/runtime/exit.S category/vm/runtime/exit.cpp category/vm/runtime/log.cpp category/vm/runtime/math.S category/vm/runtime/selfdestruct.cpp category/vm/runtime/storage.cpp category/vm/runtime/transmute.S category/crypto/keccak.c category/crypto/keccak_impl.S"
comp() {
 case $1 in
  *.S) clang -c $INC $ARCH $1 -o $2 ;;
  *.c) gcc -std=c2x -O2 $ARCH -D_GNU_SOURCE $INC -c $1 -o $2 ;;
  *) $CXX $CXXF -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $1 -o $2 ;;
 esac || echo "FAILED $1" >> $OUT/errors.txt
}
rm -f $OUT/errors.txt
# gcc 13 cannot build the interpreter (needs musttail). asmdump only compiles, so with g++ the interpreter object is left out.
[ $CXX = g++ ] && VM=$(echo $VM | tr " " "\n" | grep -v interpreter/execute.cpp | tr "\n" " ")
for f in $VM; do o=$OUT/vm/$(echo $f | tr / _).o; [ -f $o ] || comp dl/monad-$VER/$f $o &
 while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 0.3; done; done
[ -f $OUT/x86_orig.o ] || comp $W/src/x86_orig.cpp $OUT/x86_orig.o &
[ -f $OUT/x86_hook.o ] || comp $W/src/x86_hook.cpp $OUT/x86_hook.o &
wait
[ -f $OUT/errors.txt ] && { cat $OUT/errors.txt; exit 1; }
$CXX $CXXF $ARCH $INC -c src/stub_bt.cpp -o $OUT/stub_bt.o || exit 1
gcc -O2 -c src/support16.c -o $OUT/support16.o || exit 1
$CXX $CXXF -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $C27/src/asmdump.cpp -o $OUT/asmdump.o || exit 1
COMMON="$OUT/vm/*.o $OUT/stub_bt.o $OUT/support16.o $AJ/*.o -lpthread"
$CXX -o $OUT/asmdump_orig $OUT/asmdump.o $OUT/x86_orig.o $COMMON || exit 1
$CXX -o $OUT/asmdump_hook $OUT/asmdump.o $OUT/x86_hook.o $COMMON || exit 1
sha256sum $OUT/asmdump_orig $OUT/asmdump_hook
