#!/bin/bash
# Fetch non-test Go files of the searched packages for forks that the Go module proxy cannot serve.
# Usage: fetch_raw.sh <owner/repo> <ref> <outdir>. File names come from the union of the geth v1.17.9, bsc v1.8.2
# and libevm trees plus fork-specific names listed below; non-200 answers are recorded in <outdir>/missing.txt.
set -u
repo=$1; ref=$2; out=$3; base=/home/user/v4-core/research/network-risk/cycles/018/theme-go-toolchain-shapes.work/dl/src
mkdir -p $out; : > $out/missing.txt; : > $out/fetched.txt; lst=$out/.list
: > $lst
for t in geth-v1.17.9 bsc-v1.8.2 libevm-d398bc4dbe41; do
  (cd $base/$t && find core/vm core/state core/types trie rlp common/math core/tracing core/blockstm -maxdepth 2 -name '*.go' ! -name '*_test.go' 2>/dev/null) >> $lst
done
for f in go.mod core/vm/interpreter_dispatch.go core/vm/jumpdests.go core/vm/keccak_cache.go core/vm/bounded_cache.go core/vm/ecrecover_cache.go core/vm/mulmod_memo.go core/state/parallel_statedb.go core/state/parallel_statedb_journal.go core/vm/celo_contracts.go core/vm/celo_contracts_helpers.go core/vm/analysis.go core/vm/analysis_legacy.go core/types/celo_transaction.go core/types/celo_dynamic_fee_tx.go core/types/rollup_cost.go core/vm/contracts_optimism.go core/blockstm/mvhashmap.go core/blockstm/executor.go core/blockstm/status.go core/blockstm/txio.go core/blockstm/dag.go; do echo $f >> $lst; done
for f in $(sort -u $lst); do
  mkdir -p $out/$(dirname $f)
  code=$(curl -s -o $out/$f -w '%{http_code}' https://raw.githubusercontent.com/$repo/$ref/$f)
  if [ "$code" = 200 ]; then echo $f >> $out/fetched.txt; else rm -f $out/$f; echo "$f $code" >> $out/missing.txt; fi
done
wc -l $out/fetched.txt $out/missing.txt
