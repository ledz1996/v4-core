#!/bin/bash
# Build of the cycle 23 harness from the sources fetched into dl/ (tools/fetchsrc.py).
# ./tools/build.sh VER COV   VER = 0.16.7 | 0.16.5, COV = 1 uses the coverage-patched emitter (src/ovVER), 0 the release file.
# Output: build/VER-cov or build/VER-plain with binaries hx (scenario harness) and rp (replay).
cd "$(dirname "$0")/.."
VER=$1; COV=$2
MONAD=dl/monad-$VER
case $VER in 0.16.7) EVMC=dl/evmc-f6b7c57e; STUBV=src/stub167; HXD="";; 0.16.5) EVMC=dl/evmc-34795f4e; STUBV=src/stub165; HXD="-DHX_STACK_T=uint8_t";; *) echo bad ver; exit 1;; esac
OUT=build/$VER-$([ "$COV" = 1 ] && echo cov || echo plain); mkdir -p $OUT build/asmjit
ARCH=-march=haswell
INC="-Idl/third -Isrc/stub -I$STUBV -I$MONAD -Idl/asmjit/src -I$EVMC/include -Idl/openssl"
VM="category/core/monad_exception.cpp category/vm/compiler/ir/basic_blocks.cpp category/vm/compiler/ir/x86.cpp category/vm/compiler/ir/x86/emitter.cpp category/vm/compiler/ir/x86/virtual_stack.cpp category/vm/evm/access_status.cpp category/vm/evm/delegation.cpp category/vm/evm/message.cpp category/vm/evm/page_storage_status.cpp category/vm/evm/revision.cpp category/vm/evm/status_code.cpp category/vm/evm/storage_status.cpp category/vm/evm/tx_context.cpp category/vm/interpreter/entry.S category/vm/interpreter/execute.cpp category/vm/interpreter/instruction_stats.cpp category/vm/interpreter/intercode.cpp category/vm/runtime/allocator.cpp category/vm/runtime/call.cpp category/vm/runtime/context.S category/vm/runtime/context.cpp category/vm/runtime/create.cpp category/vm/runtime/data.cpp category/vm/runtime/environment.cpp category/vm/runtime/exit.S category/vm/runtime/exit.cpp category/vm/runtime/log.cpp category/vm/runtime/math.S category/vm/runtime/selfdestruct.cpp category/vm/runtime/storage.cpp category/vm/runtime/transmute.S category/crypto/keccak.c category/crypto/keccak_impl.S"
for f in $VM; do s=$MONAD/$f; [ "$COV" = 1 ] && [ -f src/ov$VER/$f ] && s=src/ov$VER/$f; [ -f $s ] || { echo "missing $s"; exit 1; }; o=$OUT/$(echo $f | tr / _).o
 [ -f $o ] && continue
 case $f in
  *.S) clang -c $INC $ARCH $s -o $o ;;
  *.c) gcc -std=c2x -O2 $ARCH -D_GNU_SOURCE $INC -c $s -o $o ;;
  *) clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $s -o $o ;;
 esac 2>&1 | grep -E 'error|fatal' | head -5 &
 while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 0.5; done
done
for f in dl/asmjit/src/asmjit/core/*.cpp dl/asmjit/src/asmjit/x86/*.cpp dl/asmjit/src/asmjit/arm/*.cpp; do o=build/asmjit/$(basename $f .cpp).o; [ -f $o ] || clang++ -std=c++17 -O2 -DASMJIT_STATIC -DNDEBUG $ARCH -Idl/asmjit/src -c $f -o $o 2>&1 | grep -E 'error' | head -3 &
 while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 0.5; done
done
wait
clang++ -std=c++23 -O2 $ARCH $INC -c src/stub_bt.cpp -o $OUT/stub_bt.o || exit 1
gcc -O2 -c src/support16.c -o $OUT/support16.o
EXTRA=""; if [ "$COV" != 1 ]; then clang++ -std=c++23 -O2 -c src/covstub.cpp -o $OUT/covstub.o; EXTRA=$OUT/covstub.o; fi
for SRC in harness replay; do
 clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC $HXD -Isrc -c src/$SRC.cpp -o $OUT/$SRC.main.o || exit 1
 B=$([ $SRC = harness ] && echo hx || echo rp)
 clang++ -o $OUT/$B $OUT/$SRC.main.o $OUT/*.cpp.o $OUT/*.S.o $OUT/*.c.o $OUT/stub_bt.o $OUT/support16.o $EXTRA build/asmjit/*.o -lpthread || exit 1
done
ls -la $OUT/hx $OUT/rp
