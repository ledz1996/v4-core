# Own check of lead L-837 (HyperEVM, the seven swaps cycle 17 did not save)

Status on 2026-11-25: the rerun is still going. This file is updated when it ends.

## What was run

`v3check_own.py` is `../hyperevm.work/v3check_rest.py` with two changes: the group list is cut to the first `STOP` groups, and every mismatch is written to `out/stageB-own.json.mismatch.jsonl` as soon as it is seen.

```bash
STOP=7000 python3 v3check_own.py out/stageB-own.json --only 'm512?' --seed 3 --limit 20000 --threads 8
```

The seed (3), the limit and the filter are the ones the cycle 17 unit used, taken from its transcript. The sample is sorted before it runs, so the first 7,000 groups are the same 7,000. The counts after 500 and 1,000 groups equal the cycle 17 log (527 and 1,049 swaps reproduced, first mismatch before group 1,000).

`v3recheck.py` reruns only the groups in the mismatch file. It rebuilds the pool's events for the block from `eth_getLogs` and reads the `0xd78218c0` Mint variant as a mint (ticks in topics 2 and 3, liquidity in data word 2), which the cycle 15 collector does not read.

```bash
python3 v3recheck.py out/stageB-own.recheck.json --threads 4
```

## Result so far

Mismatch 1: transaction `0x000afdd95fae334b3e95f4eb248c1c3197b598bc7d101643aef3aa2093fef434`, block 50,505,119, pool `0x0d3e8f6949dcaca02cbd1aaf7ca840f4f36216b7`. The block holds a `0xd78218c0` Mint variant at ticks 199185 to 199190 with liquidity 12,304,701,949,129,529 before the swap. The parent liquidity 5,751,706,501,937,840 plus that amount is 18,056,408,451,067,369, the liquidity the swap logs. With the event applied, the swap reproduces price, tick, liquidity and both amounts to the unit, with two calls on the 512-bit branch of `mulDiv`. It is a collector gap, the same cause as the four mismatches of cycle 15.
