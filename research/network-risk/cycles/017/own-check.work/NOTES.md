# Own check of lead L-837 (HyperEVM, the seven swaps cycle 17 did not save)

Status on 2026-11-25: finished. All seven swaps are collector gaps and reproduce to the unit once the missing event is read.

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

## Result

The rerun gives the counts of the cycle 17 log exactly: 7,000 groups, 7,282 swaps reproduced, 1,625 of them with several steps, 3,008 with a call on the 512-bit branch of `mulDiv`, and 7 mismatches. The seven records are in `results/mismatches.jsonl`.

Six are in pool `0x0d3e8f6949dcaca02cbd1aaf7ca840f4f36216b7` (blocks 50,505,119, 50,908,746, 50,964,817, 51,001,977, 51,126,394 and 51,184,294) and one in pool `0x12e5f773134a6df0fcc74aedddcca0429a08eaa6` (block 50,897,298). Every one of the seven blocks holds a `0xd78218c0` Mint variant for the pool before the swap, and no other topic the collector does not read.

`v3recheck.py` with the variant read as a mint reproduces all seven: price, tick, liquidity and both amounts equal the log to the unit (`results/recheck.json`). Two of the seven are swaps with several steps, and two make calls on the 512-bit branch of `mulDiv` (four calls). Nothing is left unexplained, so the sample holds no sign that the validator's arithmetic differs from `src/libraries/FullMath.sol` or `SqrtPriceMath.sol`.

Worked example, mismatch 1: transaction `0x000afdd95fae334b3e95f4eb248c1c3197b598bc7d101643aef3aa2093fef434`. The block holds a Mint variant at ticks 199185 to 199190 with liquidity 12,304,701,949,129,529. The parent liquidity 5,751,706,501,937,840 plus that amount is 18,056,408,451,067,369, the liquidity the swap logs.

## What this does not settle

About 57,000 groups of the same kind have not been rerun by any cycle. Cycle 18 (theme-hyperevm-v3-rest) runs them with the variant read. Four of the seven matches, like most matches in the sample, come from the fee search: the pool charges a fee other than `fee()`, the script finds the fee in pips that lands on the logged price, and then requires all five logged values to match at that fee.
