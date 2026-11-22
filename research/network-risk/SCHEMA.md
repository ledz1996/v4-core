# File formats for one cycle

Agents write these files into `research/network-risk/cycles/<NNN>/` and run `python3 research/network-risk/tools/validate.py <kind> <file>` until it prints `OK`.

## `<unit>.research.json` (kind `research`)

```json
{
  "unit": "op-stack-eth",
  "profiles": [
    {"chainId": 10, "lens": "L1", "summary": "one to three sentences",
     "deltas": [{"delta": "what differs from Ethereum mainnet", "source": "https://...", "relevance": "none|low|high"}]}
  ],
  "findings": [
    {"ref": "new or an existing id such as F-007",
     "title": "sentence case, names the mechanism",
     "chainIds": [10, 8453],
     "lens": "L3",
     "assumptions": ["A2", "A6"],
     "effect": "siphon|freeze|both|degrade",
     "actor": "unprivileged|pool-creator|issuer|operator|governance",
     "severity": "critical|high|medium|low|info",
     "difference": "what this network does that Ethereum does not",
     "mechanism": "how that difference meets the PoolManager code, step by step, no exploit code",
     "impact": "which funds, how much of them, who loses",
     "preconditions": "what must be true, and who must act",
     "mitigations": "what the deployer, pool creators or LPs can do",
     "coreRefs": ["src/PoolManager.sol:349-364"],
     "sources": [{"url": "https://...", "supports": "the fact this source backs"}],
     "evidence": "primary|secondary|inferred"}
  ],
  "cleared": [
    {"chainIds": [10], "lens": "L2", "check": "what was tested", "result": "why it is safe", "source": "https://... or file:line"}
  ],
  "leads": [
    {"chainIds": [10], "lens": "L4", "question": "one concrete open question", "why": "what it could lead to", "priority": "high|medium|low"}
  ],
  "leadResults": [
    {"leadId": "L-012", "outcome": "finding|cleared|inconclusive", "answer": "what was found"}
  ]
}
```

Every `(chainId, lens)` pair assigned to the unit needs one `profiles` entry. Every finding needs at least one `coreRefs` entry and one `sources` entry.

## `<unit>.verdicts.json` (kind `verdicts`)

```json
{
  "unit": "op-stack-eth",
  "verdicts": [
    {"findingIndex": 0,
     "verdict": "confirmed|plausible|refuted",
     "severity": "critical|high|medium|low|info",
     "factCheck": "what the primary sources say, with what was fetched or queried",
     "codeCheck": "what the code path in src/ does, with file:line",
     "corrections": "anything the finding got wrong; empty string if nothing",
     "sources": [{"url": "https://...", "supports": "..."}]}
  ],
  "clearedSpotChecks": [
    {"check": "text of the cleared item", "agrees": true, "note": "why"}
  ],
  "leads": []
}
```

`findingIndex` is the position in the research file's `findings` array. Every finding gets a verdict.

## `critic.json` (kind `critic`)

```json
{
  "gaps": [{"chainIds": [999], "lens": "L2", "note": "what is thin or missing"}],
  "duplicates": [{"titles": ["...", "..."], "note": "same hazard reported twice"}],
  "leads": [{"chainIds": [137], "lens": "L3", "question": "...", "why": "...", "priority": "high"}]
}
```

## Actor

`actor` names the least privileged party that can trigger the hazard. Only `unprivileged` is in scope for the review's goal. The others are recorded for reference.

- unprivileged: any account. It may deploy contracts and send public transactions, and the victims did nothing unusual (they used a pool that has no attacker-made hook or token).
- pool-creator: the attacker must be the author of a hook or token that the victims chose to use.
- issuer: needs admin keys of a token that pools hold.
- operator: needs a sequencer, block builder, validator or bridge committee.
- governance: needs the PoolManager owner, the fee controller or chain governance.

## Severity

- critical: an unprivileged party can take pool funds, or freeze them for good, under conditions that hold today.
- high: loss or freeze needs a privileged chain-level actor (token issuer, sequencer, validator set, chain governance) or a specific pool or token setup that people would realistically create.
- medium: loss limited to particular pools or integrations, or liquidity operations blocked without loss.
- low: operational or integration hazard with no direct loss path found.
- info: a difference that was checked and does not create a hazard.

## Verdicts

- confirmed: the chain fact is backed by a primary source or an on-chain query, and the code path was read and does what the finding says.
- plausible: the mechanism is sound but one link could not be confirmed.
- refuted: a primary source or the code contradicts the finding. Refuted findings stay in the ledger so they are not raised again.

## Prose style

Write every prose field in plain declarative sentences. State the fact and the consequence. Do not use em dashes or en dashes, "not X but Y" contrasts, rhetorical closers, bold text, or words such as crucial, robust, key, landscape, highlight, underscore. Titles are sentence case. If you could not confirm something, say which part.
