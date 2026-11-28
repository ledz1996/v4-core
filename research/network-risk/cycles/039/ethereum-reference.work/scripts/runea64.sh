#!/bin/bash
# cycle 39: erigon v3.8.2 linux arm64 release, core/vm handlers and holiman/uint256 functions in the AArch64 model (c38/drive.py, target erigon-arm64)
cd "$(dirname "$0")/.."
for s in battery targeted c27 v4shapes random direct ruint121 provevec pow2; do echo $s; done | xargs -P ${PAR:-3} -I{} bash -c "python3 -I scripts/c38/drive.py erigon-arm64 {} 0 1 out/erigon-a64/{}.json >> out/erigon-a64/progress.log 2>&1 || echo FAILED {} >> out/erigon-a64/progress.log"
echo ALLDONE >> out/erigon-a64/progress.log
