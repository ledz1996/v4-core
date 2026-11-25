cd "$(dirname "$0")"
INC="-Idl/third -Istub -Idl/monad -Idl/asmjit/src -Idl/evmc/include"
CXX="clang++ -std=c++23 -O1 -DASMJIT_STATIC -DNDEBUG -mavx2 -mbmi2 -mlzcnt -madx $INC"
for f in "$@"; do o=build/$(echo $f | tr / _ ).o; $CXX -c $f -o $o 2>&1 | grep -E 'error|fatal' | head -8; done
