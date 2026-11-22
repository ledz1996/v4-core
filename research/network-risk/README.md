# Network risk review for the PoolManager

This directory holds a standing review of one question: on which of the 21 networks where Uniswap v4 is officially deployed could funds held by this repository's PoolManager be frozen or siphoned, and why.

The review runs in cycles. Each cycle reads the state left by the one before it, does a bounded amount of new work, and writes the state back. Nothing depends on a single long session, so the loop can run for as long as someone keeps starting cycles.

## Where to look

| File | What it is |
|---|---|
| `REPORT.md` | The report for people. Findings by severity, then by network. |
| `STATUS.md` | Generated dashboard: findings index, coverage matrix, open leads, cycle history. |
| `ASSUMPTIONS.md` | What the code in `src/` assumes about the chain, with line numbers. Every agent starts here. |
| `SCHEMA.md` | File formats, the severity scale, verdict definitions, prose style. |
| `state/networks.json` | The 21 networks, their PoolManager addresses and facts read from chain. |
| `state/ledger.json` | Coverage per network and lens, the lead queue, cycle history. |
| `state/findings.json` | Every finding ever raised, including refuted ones. |
| `state/cleared.json` | Differences that were checked and found safe, with the reason. |
| `cycles/NNN/` | Raw output of cycle NNN: the plan, one research file and one verdict file per unit, and the critic's notes. |
| `workflow/cycle.js` | The workflow script for one cycle. |
| `tools/` | `plan.py`, `validate.py`, `merge.py`, `status.py`, `probe.py`. |
| `style/humanizer-SKILL.md` | The writing guide used for the report (MIT, from github.com/blader/humanizer). |

## One cycle

1. Plan. `python3 research/network-risk/tools/plan.py <date>` prints the work for the next cycle as JSON. Save it as `cycles/NNN/plan.json`.
2. Run. Start the workflow `workflow/cycle.js` with that JSON as `args`. It runs one research agent per chosen network family, one or two agents that re-read the source itself, an independent verifier behind each of them, and a critic at the end. Agents write their output into `cycles/NNN/` and validate it with `tools/validate.py`.
3. Merge. `python3 research/network-risk/tools/merge.py research/network-risk/cycles/NNN <date>` folds the cycle into `state/` and regenerates `STATUS.md`.
4. Report. Update `REPORT.md` for every finding that is new or changed status. Follow `style/humanizer-SKILL.md`.
5. Commit and push `research/network-risk/`.

Every fourth cycle, before planning, re-run the chain probe to catch drift:

```bash
python3 -I research/network-risk/tools/probe.py <dir-with-deployments.txt-and-chains.json> <out.json>
```

Compare the result with `state/networks.json`. A new network on the deployments page, a changed bytecode hash, a new owner or fee controller, or a changed block gas limit each become a high priority lead. A new network gets its own cells at depth 0, which makes the planner schedule a baseline for it.

## Why the queue does not run dry

The planner scores each network family and picks the top four. Four things keep feeding it.

Cells start at depth 0 and a baseline pass only brings them to depth 2. Reaching depth 3 takes a revisit.

Every research agent, verifier and critic writes leads: concrete open questions with a priority. A lead stays open until an agent answers it with a finding or a clearance. After three inconclusive attempts it is parked.

Findings marked plausible or unverified pull their network family back into the plan until someone confirms or refutes them. Confirmed findings are re-checked after six cycles, because networks upgrade.

Revisits rotate through two lenses and one of eight angles (hostile token issuer, hostile sequencer, upcoming network upgrade, hook author using chain-only features, client source reading, new transaction types, and so on). The same network gets different questions each time.

Separately, one source-reading unit runs every cycle and alternates between the accounting files and the math files.

## Rules the agents work under

Read the code in this repository as written. Do not diff it against upstream v4-core or any other copy.

Analysis only. No exploit code, no transactions. Read-only RPC calls are fine.

Every chain fact needs a source that was fetched, or an on-chain query that was run. Every code claim needs a file and line.

A finding is confirmed only when a second agent, working independently, checked both the chain fact and the code path.

Refuted findings and cleared checks are kept, so later cycles do not raise them again.
