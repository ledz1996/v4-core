cd "$(dirname "$0")"
mkdir -p build/asmjit
for f in dl/asmjit/src/asmjit/core/*.cpp dl/asmjit/src/asmjit/x86/*.cpp; do o=build/asmjit/$(basename $f .cpp).o; clang++ -std=c++17 -O1 -DASMJIT_STATIC -DASMJIT_NO_AARCH64 -fno-exceptions -Idl/asmjit/src -c $f -o $o 2>&1 | grep -E 'error' | head -3 & done; wait
