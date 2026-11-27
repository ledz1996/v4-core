#!/bin/bash
# Cycle 28: full rebuild of the cycle 27 fixed harness (cycles/027/theme-monad-engine-agreement.work/src/harness_fixed.cpp)
# from the Monad source already fetched by cycle 23 (cycles/023/theme-monad-compiled-coverage.work/dl), with the
# compilers present (clang++, gcc). Nothing is downloaded. Every object is compiled fresh into this work dir.
# Same flags as cycle 23 tools/build.sh and cycle 27 scripts/build.sh.
# Usage: scripts/build.sh VER   -> build/VER/{hxf,hxfcov} (hxfcov links the cycle 23 coverage-labelled emitter src/ovVER)
W=$(cd "$(dirname "$0")/.." && pwd)
C23=$(cd $W/../../023/theme-monad-compiled-coverage.work && pwd)
C27=$(cd $W/../../027/theme-monad-engine-agreement.work && pwd)
VER=$1
case $VER in 0.16.7) EVMC=dl/evmc-f6b7c57e; STUBV=src/stub167; HXD="";; 0.16.5) EVMC=dl/evmc-34795f4e; STUBV=src/stub165; HXD="-DHX_STACK_T=uint8_t";; *) echo bad; exit 1;; esac
cd $C23
OUT=$W/build/$VER; mkdir -p $OUT/vm $OUT/cov $W/build/asmjit
ARCH=-march=haswell
INC="-Idl/third -Isrc/stub -I$STUBV -Idl/monad-$VER -Idl/asmjit/src -I$EVMC/include -Idl/openssl"
VM="category/core/monad_exception.cpp category/vm/compiler/ir/basic_blocks.cpp category/vm/compiler/ir/x86.cpp category/vm/compiler/ir/x86/emitter.cpp category/vm/compiler/ir/x86/virtual_stack.cpp category/vm/evm/access_status.cpp category/vm/evm/delegation.cpp category/vm/evm/message.cpp category/vm/evm/page_storage_status.cpp category/vm/evm/revision.cpp category/vm/evm/status_code.cpp category/vm/evm/storage_status.cpp category/vm/evm/tx_context.cpp category/vm/interpreter/entry.S category/vm/interpreter/execute.cpp category/vm/interpreter/instruction_stats.cpp category/vm/interpreter/intercode.cpp category/vm/runtime/allocator.cpp category/vm/runtime/call.cpp category/vm/runtime/context.S category/vm/runtime/context.cpp category/vm/runtime/create.cpp category/vm/runtime/data.cpp category/vm/runtime/environment.cpp category/vm/runtime/exit.S category/vm/runtime/exit.cpp category/vm/runtime/log.cpp category/vm/runtime/math.S category/vm/runtime/selfdestruct.cpp category/vm/runtime/storage.cpp category/vm/runtime/transmute.S category/crypto/keccak.c category/crypto/keccak_impl.S"
comp() { # src obj
 case $1 in
  *.S) clang -c $INC $ARCH $1 -o $2 ;;
  *.c) gcc -std=c2x -O2 $ARCH -D_GNU_SOURCE $INC -c $1 -o $2 ;;
  *) clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $1 -o $2 ;;
 esac || echo "FAILED $1" >> $OUT/errors.txt
}
rm -f $OUT/errors.txt
for f in $VM; do o=$OUT/vm/$(echo $f | tr / _).o; [ -f $o ] || comp dl/monad-$VER/$f $o &
 while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 0.3; done; done
o=$OUT/cov/emitter_cov.o; [ -f $o ] || comp src/ov$VER/category/vm/compiler/ir/x86/emitter.cpp $o &
for f in dl/asmjit/src/asmjit/core/*.cpp dl/asmjit/src/asmjit/x86/*.cpp dl/asmjit/src/asmjit/arm/*.cpp; do o=$W/build/asmjit/$(basename $f .cpp).o
 [ -f $o ] || clang++ -std=c++17 -O2 -DASMJIT_STATIC -DNDEBUG $ARCH -Idl/asmjit/src -c $f -o $o &
 while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 0.3; done; done
wait
[ -f $OUT/errors.txt ] && { cat $OUT/errors.txt; exit 1; }
clang++ -std=c++23 -O2 $ARCH $INC -c src/stub_bt.cpp -o $OUT/stub_bt.o || exit 1
gcc -O2 -c src/support16.c -o $OUT/support16.o || exit 1
clang++ -std=c++23 -O2 -c src/covstub.cpp -o $OUT/covstub.o || exit 1
clang++ -std=c++23 -O2 -g -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC $HXD -Isrc -c $C27/src/harness_fixed.cpp -o $OUT/harness_fixed.o || exit 1
COMMON="$(ls $OUT/vm/*.o | grep -v x86_emitter) $OUT/stub_bt.o $OUT/support16.o $W/build/asmjit/*.o -lpthread"
clang++ -o $OUT/hxf $OUT/harness_fixed.o $OUT/vm/category_vm_compiler_ir_x86_emitter.cpp.o $OUT/covstub.o $COMMON || exit 1
clang++ -o $OUT/hxfcov $OUT/harness_fixed.o $OUT/cov/emitter_cov.o $COMMON || exit 1
sha256sum $OUT/hxf $OUT/hxfcov
