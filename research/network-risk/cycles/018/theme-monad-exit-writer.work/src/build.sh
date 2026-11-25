#!/bin/bash
# Links the cycle 16 v0.16.5 objects (submodule pins asmjit e8c8e2e4, evmc 34795f4e, release keccak) with the
# instrumented emitter (src/patch_writer.py) into: build/orders (compile-only), build/rp165w (mined replay),
# build/hx165w (scenario harness). Nothing outside this work directory is written.
set -e
W=$(cd "$(dirname "$0")/.." && pwd); W16=$(realpath $W/../../016/theme-monad-harness-exact.work)
MONAD=$W16/dl/monad-0.16.5; OBJ=$W16/build/v165
INC="-I$W16/dl/third -I$W16/stub -I$W16/stub165 -I$MONAD -I$W16/dl/asmjit/src -I$W16/dl/evmc165/include -I$W16/dl/openssl"
FL="-std=c++23 -DHX_STACK_T=uint8_t -O2 -DASMJIT_STATIC -DNDEBUG -D_GNU_SOURCE -march=haswell -Wno-switch"
O=$W/build/v165w
python3 $W/src/patch_writer.py $W/build/p165/emitter.orig.cpp $W/build/p165/emitter.cpp
clang++ $FL $INC -c $W/build/p165/emitter.cpp -o $O/emitter_hxw.o
clang++ $FL $INC -c $W/src/orders.cpp -o $O/orders.o; clang++ -O2 -c $W/src/hxw_env.cpp -o $O/hxw_env.o
( cd $W16; clang++ $FL -DHX_STACK_T=uint8_t $INC -c replay.cpp -o $O/replay.o; clang++ $FL $INC -c harness.cpp -o $O/harness.o )
OBJS=$(ls $OBJ/*.cpp.o $OBJ/*.S.o $OBJ/*.c.o | grep -v -e compiler_ir_x86_emitter.cpp.o)
for m in orders replay harness; do E=""; [ $m = orders ] || E=$O/hxw_env.o
  clang++ -o $W/build/$m-165w $O/$m.o $E $O/emitter_hxw.o $OBJS $OBJ/stub_bt.o $OBJ/support16.o $OBJ/asmjit/*.o -lpthread
done
ls -la $W/build/*-165w
