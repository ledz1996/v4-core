#!/bin/bash
# Build of the cycle 16 harness: monad v0.16.7 (or $MONAD) vm sources, asmjit e8c8e2e4 (submodule pin of v0.16.7 and v0.16.5),
# category-labs/evmc f6b7c57e (pin of v0.16.7) or 34795f4e (pin of v0.16.5), real keccak (keccak.c + keccak_impl.S, OpenSSL AVX2 or AVX512).
cd "$(dirname "$0")"
MONAD=${MONAD:-dl/monad}; EVMC=${EVMC:-dl/evmc}; OUT=${OUT:-build/v167}; ARCH=${ARCH:--march=haswell}; CC=${CC:-clang}; CXX=${CXX:-clang++}
mkdir -p $OUT/asmjit
INC="-Idl/third -Istub -I${STUBV:-stub167} -I$MONAD -Idl/asmjit/src -I$EVMC/include -Idl/openssl"
VM="category/core/monad_exception.cpp category/vm/compiler/ir/basic_blocks.cpp category/vm/compiler/ir/x86.cpp category/vm/compiler/ir/x86/emitter.cpp category/vm/compiler/ir/x86/virtual_stack.cpp category/vm/evm/access_status.cpp category/vm/evm/delegation.cpp category/vm/evm/message.cpp category/vm/evm/page_storage_status.cpp category/vm/evm/revision.cpp category/vm/evm/status_code.cpp category/vm/evm/storage_status.cpp category/vm/evm/tx_context.cpp category/vm/interpreter/entry.S category/vm/interpreter/execute.cpp category/vm/interpreter/instruction_stats.cpp category/vm/interpreter/intercode.cpp category/vm/runtime/allocator.cpp category/vm/runtime/call.cpp category/vm/runtime/context.S category/vm/runtime/context.cpp category/vm/runtime/create.cpp category/vm/runtime/data.cpp category/vm/runtime/environment.cpp category/vm/runtime/exit.S category/vm/runtime/exit.cpp category/vm/runtime/log.cpp category/vm/runtime/math.S category/vm/runtime/selfdestruct.cpp category/vm/runtime/storage.cpp category/vm/runtime/transmute.S category/crypto/keccak.c category/crypto/keccak_impl.S"
for f in $VM; do s=$MONAD/$f; [ -f $s ] || { [ -f dl/monad/$f ] && s=dl/monad/$f; }; o=$OUT/$(echo $f | tr / _).o
 case $f in
  *.S) $CC -c $INC -Idl/openssl $ARCH $s -o $o ;;
  *.c) gcc -std=c2x -O2 $ARCH -D_GNU_SOURCE $INC -c $s -o $o ;;
  *) $CXX -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE $ARCH -Wno-switch $INC -c $s -o $o ;;
 esac 2>&1 | grep -E 'error|fatal' | head -5 &
done
for f in dl/asmjit/src/asmjit/core/*.cpp dl/asmjit/src/asmjit/x86/*.cpp dl/asmjit/src/asmjit/arm/*.cpp; do o=$OUT/asmjit/$(basename $f .cpp).o; [ -f $o ] || $CXX -std=c++17 -O2 -DASMJIT_STATIC -DNDEBUG $ARCH -Idl/asmjit/src -c $f -o $o 2>&1 | grep -E 'error' | head -3 & done
wait
