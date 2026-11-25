cd "$(dirname "$0")"
INC="-Idl/third -Istub -Idl/monad-0.16.5 -Idl/asmjit/src -Idl/evmc/include"
for f in "$@"; do o=build165/$(basename $(dirname $f))_$(basename $f).o
case $f in
 *.S) clang -c $INC -mavx2 $f -o $o ;;
 *.c) clang -std=c2x -O2 -mavx2 -mbmi2 $INC -c $f -o $o ;;
 *) clang++ -std=c++23 -O2 -DASMJIT_STATIC -DNDEBUG -mavx2 -mbmi2 -mlzcnt -madx -Wno-switch $INC -c $f -o $o ;;
esac 2>&1 | grep -E 'error|fatal' | head -5 &
done; wait
