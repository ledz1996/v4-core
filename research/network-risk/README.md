# Network risk review for the PoolManager

This directory holds a standing review of one question: on which of the 21 networks where Uniswap v4 is officially deployed could an ordinary account freeze or siphon funds that other users hold in this repository's PoolManager, and why.

The attacker has no role: no owner or fee controller keys, no token admin keys, no sequencer or validator power, no governance vote. The victims are ordinary liquidity providers, swappers and holders of ERC-6909 claims. Hazards that need a privileged party are recorded with an `actor` label and kept out of the main findings.

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
| `state/themes.json` | Cross-network questions queued by hand from the high priority leads. Up to three open ones run per cycle. |
| `state/cleared.json` | Differences that were checked and found safe, with the reason. |
| `cycles/NNN/` | Raw output of cycle NNN: the plan, one research file and one verdict file per unit, and the critic's notes. |
| `workflow/cycle.js` | The workflow script for one cycle. |
| `tools/` | `plan.py`, `validate.py`, `merge.py`, `status.py`, `probe.py`. |
| `style/humanizer-SKILL.md` | The writing guide used for the report (MIT, from github.com/blader/humanizer). |

## One cycle

0. Once per fresh checkout: `git submodule update --init --depth 1 lib/solmate`, so the readers can see `Owned.sol`.
1. Plan. `python3 research/network-risk/tools/plan.py <date>` writes `cycles/NNN/plan.json` and prints a compact JSON object. Options: `--all` takes every network family instead of the top four, `--angles 0,1,2,3` forces specific work items, `--readings N` sets how many code readings run. `--units a,b,c` takes exactly the named network families. `--themes N` sets how many open themes run (default three).
2. Run. Start the workflow `workflow/cycle.js` with the printed JSON as `args`. It runs one research agent per chosen network family, one or two agents that re-read the source itself, an independent verifier behind each of them, and a critic at the end. Agents write their output into `cycles/NNN/` and validate it with `tools/validate.py`.
3. Merge. `python3 research/network-risk/tools/merge.py research/network-risk/cycles/NNN <date>` folds the cycle into `state/` and regenerates `STATUS.md`.
4. Report. Rewrite `report/front.md` by hand (the answer so far, what was tested, what is open), following `style/humanizer-SKILL.md`, then run `python3 research/network-risk/tools/report.py`. It renders `REPORT.md`, `FINDINGS.md` and `CLEARED.md` from the ledger and lints the prose.
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

A finding that names an earlier one in "ref" replaces it only when the plan assigned that recheck to the unit. Otherwise it is kept as its own entry with an "extends" link. `cycles/NNN/skip.json` drops a finding that the critic showed to be a second report of one event. `cycles/NNN/extends.json` links a finding to an earlier one when the agent did not, `actors.json` applies an actor that a verifier corrected, and `severity.json` sets one severity for findings of a class that was rated unevenly; the verifier's rating stays in the entry.

If a run loses agents to an outage, start the workflow again with the same JSON plus a `done` object that lists the units whose research or verdict file already exists, for example `"done": {"research": ["op-stack-eth"], "verify": []}`. Only the missing agents run, and the critic updates its earlier file.

Findings marked plausible or unverified pull their network family back into the plan until someone confirms or refutes them. Confirmed findings are re-checked after six cycles, because networks upgrade.

Revisits rotate through eight work items: a sweep of the chain's special addresses with the PoolManager as caller, an opcode comparison against the node's source, the faces of the native asset, known weaknesses of the network, added transaction types, upcoming forks, the assets pools hold, and ways to block other users' exits. The same network gets different questions each time.

Separately, two readings of the source run every cycle and rotate through six directions: two file-by-file passes, a swap trace, a liquidity trace, an attempt to break the custody invariants, and a check of every mask, shift and cast.

## Rules the agents work under

Read the code in this repository as written. Do not diff it against upstream v4-core or any other copy.

Analysis only. No exploit code, no transactions. Read-only RPC calls are fine.

Every chain fact needs a source that was fetched, or an on-chain query that was run. Every code claim needs a file and line.

A finding is confirmed only when a second agent, working independently, checked both the chain fact and the code path.

Refuted findings and cleared checks are kept, so later cycles do not raise them again.
