#!/bin/bash
# Rerun the shape search over every downloaded tree. Output: out/scan-<tree>.json and out/scan.log
set -u
W=$(cd $(dirname $0)/.. && pwd); S=$W/dl/src; B=$W/scripts/shapescan/shapescan
mkdir -p $W/out; : > $W/out/scan.log
pk(){ (cd $S/$1 && for d in core/vm core/vm/runtime core/state core/types trie trie/trienode rlp common/math core/blockstm core/tracing libevm libevm/stateconf libevm/hookstest triedb/pathdb triedb/hashdb core/state/snapshot plugin/evm/customtypes nativeasset params precompile/contract; do [ -d $d ] && ls $d/*.go >/dev/null 2>&1 && echo $d; done); }
run(){ name=$1; root=$S/$1; mod=$2; u=$S/$3; shift 3; $B $name $root $mod $u "$@" > $W/out/scan-$name.json 2>> $W/out/scan.log; }
run uint256-v1.3.2 github.com/holiman/uint256 uint256-v1.3.2 .
run uint256-v1.2.4 github.com/holiman/uint256 uint256-v1.2.4 .
run geth-v1.17.9 github.com/ethereum/go-ethereum uint256-v1.3.2 $(pk geth-v1.17.9)
run bsc-v1.8.2 github.com/ethereum/go-ethereum uint256-v1.3.2 $(pk bsc-v1.8.2)
run bor-v2.11.1 github.com/ethereum/go-ethereum uint256-v1.3.2 $(pk bor-v2.11.1)
run celo-op-geth-c7ed55b8 github.com/ethereum/go-ethereum uint256-v1.3.2 $(pk celo-op-geth-c7ed55b8)
run libevm-d398bc4dbe41 github.com/ava-labs/libevm uint256-v1.2.4 $(pk libevm-d398bc4dbe41)
run graft-evm-v1.15.3 github.com/ava-labs/avalanchego/graft/evm uint256-v1.2.4 $(pk graft-evm-v1.15.3)
run coreth-v1.15.3 github.com/ava-labs/avalanchego/graft/coreth uint256-v1.2.4 $(pk coreth-v1.15.3)
cat $W/out/scan.log
