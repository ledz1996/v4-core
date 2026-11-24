export const meta = {
  name: 'v4-network-risk-cycle',
  description: 'One cycle of the PoolManager network risk review: research per network family and per code reading, independent verification, gap critic',
  whenToUse: 'Run with the JSON printed by research/network-risk/tools/plan.py as args. One run is one cycle of the endless review loop.',
  phases: [
    { title: 'Research', detail: 'one agent per network family, plus readers of the source itself' },
    { title: 'Verify', detail: 'an independent agent tries to refute each finding' },
    { title: 'Critic', detail: 'finds gaps and writes leads for the next cycle' },
  ],
}

const plan = typeof args === 'string' ? JSON.parse(args) : args
const ROOT = 'research/network-risk'
const DIR = plan.dir

const SUMMARY = {
  type: 'object',
  properties: {
    file: { type: 'string' },
    validated: { type: 'boolean' },
    findings: { type: 'number' },
    inScope: { type: 'number' },
    headline: { type: 'string' },
  },
  required: ['file', 'validated', 'findings', 'inScope', 'headline'],
}

// "model" in the args runs every agent of the cycle on that model (used when the session model is out of quota).
const MODEL = plan.model ? { model: plan.model } : {}
// The owner of the review narrowed its focus on 2026-11-24. Cycles planned with "focus": "opcodes" carry this paragraph.
const FOCUS = plan.focus === 'opcodes' ? `
Focus of this cycle, set by the owner of the review: the network itself, its opcodes and how its client implements them, and what that does to the arithmetic and the logic of the code in src/. Earlier cycles spent most of their effort on particular tokens and third-party hooks; that is no longer wanted. Do not sweep tokens or hooks, and record a token or hook hazard you happen to meet in one line. Spend the time on: the interpreter and any compiler, bytecode rewriting, code analysis or cache in front of it; the 256 bit integer library and its version; results of MULMOD, ADDMOD, DIV, SDIV, MOD, SMOD, SIGNEXTEND, SAR, SHL, SHR, BYTE, EXP and the comparisons at their edges; JUMP and JUMPI with jump destination analysis; KECCAK256, MCOPY, memory, calldata and return data operations; storage and transient storage semantics; gas rules only where they change what a call returns; and, for each difference or past fault, which line of src/libraries (TickMath, BitMath, FullMath, UnsafeMath, SqrtPriceMath, SwapMath, TickBitmap, Position, LiquidityMath, Pool) or of the settlement code would compute or decide something else because of it. Read ${ROOT}/OPCODES.md first: it holds what is already tested and read (a battery of 185,529 opcode vectors on all 21 networks, the same PoolManager bytecode run under identical state on every network, 99,903 mined swaps checked against the source's math, and readings of several clients) and what is not yet covered. Build on it, use the scripts in ${ROOT}/tools/opdiff (run them only for your own chain ids, and write outputs to your work directory), and do not repeat what it already settles.
` : ''
const COMMON = `
You are part of a defensive security review. The repository at /home/user/v4-core holds the Solidity source of a Uniswap v4 style PoolManager. This build is a CTF variant that will be deployed to 21 EVM networks. The organisers say a weakness has been planted that is really usable on at least one of those networks, and that it follows from how that network differs from Ethereum (opcodes, precompiles, system contracts, the node's own source, known network weaknesses). The review must find it, and every other path like it, so it can be closed before deployment. Analysis only: do not write exploit code or proof-of-concept contracts, and do not send transactions. Read-only JSON-RPC calls (eth_call including the "from" field and state overrides, eth_getCode, eth_getStorageAt, eth_getBlockByNumber, debug_traceCall where the endpoint allows it) are fine and encouraged.

Threat model
- The attacker is an ordinary account. It can deploy contracts, tokens and hooks, create pools, and send any transaction the network accepts from the public. It holds no role: it is not the PoolManager owner or fee controller, not a token issuer or admin, not a sequencer, validator, block builder or bridge signer, and it controls no governance vote.
- The victims are ordinary users: liquidity providers, swappers and holders of ERC-6909 claims, above all those in pools that use no attacker-made hook and no attacker-made token.
- In scope: the attacker takes funds held by the PoolManager that belong to others, or leaves others unable to withdraw. Record hazards that need a privileged party only briefly, with the right "actor" value, and spend your time on the unprivileged ones.

Ground rules
- Read the code in this repository as it is written. Treat every line as unreviewed and do not trust your memory of Uniswap v4. Never diff or compare this code against upstream v4-core or any other copy; the owner of this review has ruled that out. Judge behaviour from the text in src/ and lib/solmate (checked out; the other lib/ submodules are empty and not needed by src/). forge is not installed; do not install anything.
- Evidence: every chain fact needs a source URL you fetched in this session (official docs, specs, improvement proposals, client source, explorers) or an on-chain query you ran, with the result. Every code claim needs a file:line in this repo that you read. Never invent a URL. If something may postdate your training data, look it up. Name any link in the reasoning you could not confirm.
- Tools: load web tools with ToolSearch (query "select:WebSearch,mcp__Exa__web_search_exa,mcp__Exa__web_fetch_exa"). curl works for public RPC endpoints, docs sites and raw.githubusercontent.com (use it to read node client source). The GitHub API and git clone of other repositories are not available.
- Do not edit anything outside ${DIR}/. Do not run git commands that change state. Do not create notes or planning files.
${FOCUS}- Read first: ${ROOT}/ASSUMPTIONS.md (threat model, what the code assumes about the chain, and the list P1 to P8 of what an ordinary caller can make the PoolManager do), ${ROOT}/SCHEMA.md (output format, the "actor" field, severity scale, prose style), ${ROOT}/state/networks.json (the 21 networks with PoolManager address, a working RPC URL and facts read from chain), ${ROOT}/state/findings.json and ${ROOT}/state/cleared.json (what earlier cycles established; filter by your chain IDs, build on it, and do not repeat it), and the "criticNotes" in ${ROOT}/state/ledger.json.
`

function researchPrompt(u) {
  const leads = u.leadIds && u.leadIds.length ? `Open leads assigned to you (look them up by id in ${ROOT}/state/ledger.json and answer each in "leadResults"; leads that only concern privileged actors can be answered in one line): ${u.leadIds.join(', ')}.` : ''
  const recheck = u.recheckIds && u.recheckIds.length ? `Findings still unsettled for your networks (settle them: re-report with "ref" set to the id and better evidence, or explain in "cleared" why they fail): ${u.recheckIds.join(', ')}.` : ''
  return `${COMMON}
Your unit: "${u.id}" (${u.title}). Chain IDs: ${u.chainIds.join(', ')}. Lenses: ${u.lenses.join(', ')} (definitions in ${ROOT}/state/ledger.json under "lenses").

Work items for this cycle: open ${DIR}/plan.json, find your unit under "units" and do the entries of its "angles" list in order.
${leads}
${recheck}

How to work
- Earlier cycles profiled these networks. Read their profiles in ${ROOT}/cycles/ (the newest *.research.json for your unit) before you start, and go deeper than they did. Where a unit has several chains, spend the most time on the chains that depart furthest from the rest of the family.
- For every difference you find, open the code path in src/ that meets it and decide: hazard, cleared, or lead. A hazard is in scope only if an ordinary account can trigger it against other users' funds.
- When a call from the PoolManager to a special address does not revert, find out exactly what it did (read the contract or client source, trace the call) and whether the caller ends up owing the PoolManager the full value that left.
- Be concrete about amounts and order of calls in "mechanism", in prose, without code.
- Put every check that came out safe in "cleared" with the reason and the evidence, so later cycles do not redo it. Put what you could not close in "leads".

Output: write ${DIR}/${u.id}.research.json in the "research" format from SCHEMA.md with "unit": "${u.id}" and "_lenses": ${JSON.stringify(u.lenses)}. Every finding needs "actor". Include one "profiles" entry for every (chainId, lens) pair assigned, holding only what is new compared with earlier cycles (an empty "deltas" list is fine when nothing is new). Run \`python3 ${ROOT}/tools/validate.py research ${DIR}/${u.id}.research.json\` and fix the file until it prints OK. Return the summary object: file path, whether validation passed, number of findings, number of findings with actor "unprivileged", and one sentence naming the most serious in-scope finding or saying there is none.`
}

function codePrompt(c) {
  return `${COMMON}
Your unit: "${c.id}". It is either a reading of the source itself (ids starting with core-code) or a question that cuts across networks (ids starting with theme). Either way the goal is a path by which an ordinary account takes or locks other users\' funds, on any of the 21 networks or on all of them.

Task: open ${DIR}/plan.json, find your unit under "code" and do what its "task" says.

How to work
- Read the actual lines, including assembly, constants, masks, casts, unchecked blocks and comparison operators. Recompute constants and do the arithmetic by hand or with python3 where a number matters.
- For a theme, work network by network through all 21 entries of networks.json, read node client source where documentation is not decisive, test on chain with read-only calls where a test exists, and say for each network whether the answer is yes, no or unknown and on what evidence.
- The tests in test/ show intended behaviour; use them to learn intent and note where source and tests disagree.
- For anything that looks wrong, work out whether it lets an ordinary account take or lock funds, on which networks, and whether a network property is needed (see ASSUMPTIONS.md and networks.json).
- Report only what the text supports. Something that looks unusual but is safe goes in "cleared" with the reason.

Output: write ${DIR}/${c.id}.research.json in the "research" format from SCHEMA.md with "unit": "${c.id}" and "profiles": []. Every finding needs "actor". Use "chainIds" for the networks affected (all 21 chain IDs from networks.json when the issue does not depend on the chain), lens "L1" for pure code issues unless another fits better, and "sources" entries of the form {"url": "src/File.sol:line", "supports": "..."} when the evidence is the code. Run \`python3 ${ROOT}/tools/validate.py research ${DIR}/${c.id}.research.json\` until it prints OK. Return the summary object.`
}

function verifyPrompt(id) {
  return `${COMMON}
You are the independent verifier for unit "${id}". Another agent wrote ${DIR}/${id}.research.json. Try to break each of its findings. You have no stake in them being right, and none in them being wrong: a real path to other users' funds must survive your check with its evidence intact.

For every entry in "findings":
1. Fact check. Fetch the cited sources and read what they say. Look for a primary source that contradicts the claim. Where the claim can be tested on chain, run the read-only query yourself against the RPC URL in networks.json.
2. Code check. Open the cited lines in src/ and trace the path yourself. Look for a guard the finding missed (for example the msg.value check in _settle, the synced-currency check in collectProtocolFees, the delta count check at the end of unlock, the int128 casts, the return data checks in Hooks and Currency).
3. Actor check. Is "actor" right? Could an ordinary account really do every step, and are the victims users who did nothing unusual?
4. Severity by the scale in SCHEMA.md.
5. Verdict: "confirmed" only when the chain fact and the code path both hold under your own reading. "plausible" when the mechanism is sound but a link is unconfirmed; say which. "refuted" when a primary source or the code contradicts it; say what. If the actor is wrong, say so in "corrections" starting with "actor: <correct value>".
Then spot-check the three "cleared" items where a mistake would cost the most. A wrongly cleared item is the most valuable thing you can find; if you find one, add it to "leads" with priority high.

Output: write ${DIR}/${id}.verdicts.json in the "verdicts" format from SCHEMA.md with "unit": "${id}" and one verdict per finding index (an empty "verdicts" array if there are no findings; still do the spot checks). Run \`python3 ${ROOT}/tools/validate.py verdicts ${DIR}/${id}.verdicts.json\` until it prints OK. Return the summary object; "findings" is the number confirmed, "inScope" the number confirmed with an unprivileged actor, and the headline names the strongest confirmed in-scope finding or says none survived.`
}

// A cycle that lost agents to an outage is finished with a second run: "done" lists what to keep.
const keepR = new Set((plan.done && plan.done.research) || [])
const keepV = new Set((plan.done && plan.done.verify) || [])
const kept = (id, kind) => ({ file: `${DIR}/${id}.${kind}.json`, validated: true, findings: -1, inScope: -1, headline: 'kept from the earlier run of this cycle' })
const RESUME = `
An earlier attempt at this unit may have left scripts and raw data in ${DIR}/<unit id>.work/. If that directory exists, read what is there first and build on it instead of collecting the same data again.`

const jobs = [
  ...plan.units.map(u => ({ id: u.id, prompt: researchPrompt(u) + RESUME })),
  ...plan.code.map(c => ({ id: c.id, prompt: codePrompt(c) + RESUME })),
]
log(`Cycle ${plan.cycle}: ${plan.units.length} network units, ${plan.code.length} code readings, each followed by a verifier, then one critic (${jobs.length * 2 + 1 - keepR.size - keepV.size} agents to run)`)

const results = await pipeline(
  jobs,
  j => keepR.has(j.id) ? kept(j.id, 'research') : agent(j.prompt, { label: `research:${j.id}`, phase: 'Research', schema: SUMMARY, ...MODEL }),
  (r, j) => (keepV.has(j.id) ? Promise.resolve(kept(j.id, 'verdicts')) : agent(verifyPrompt(j.id), { label: `verify:${j.id}`, phase: 'Verify', schema: SUMMARY, ...MODEL }))
    .then(v => ({ id: j.id, research: r, verify: v })),
)

const done = results.filter(Boolean)
const dropped = jobs.filter(j => !done.find(d => d.id === j.id)).map(j => j.id)
if (dropped.length) log(`Units that did not finish and are not covered this cycle: ${dropped.join(', ')}`)

phase('Critic')
const critic = await agent(`${COMMON}
You are the completeness critic for cycle ${plan.cycle}. Read every *.research.json and *.verdicts.json in ${DIR}/, plus ${ROOT}/state/ledger.json.
Units that failed to produce output this cycle: ${dropped.length ? dropped.join(', ') : 'none'}.

Produce the work list for the next cycle, with the threat model in mind (ordinary attacker, ordinary victims):
1. Gaps: (chainId, lens) pairs where the sweep of special addresses, the opcode comparison or the native-asset analysis is thin, rests on secondary sources, or skipped something you know of or can find quickly.
2. Transfer: a behaviour found on one network that probably exists on another where nobody checked. Name both.
3. Unsettled: findings left "plausible", and the single fact that would settle each.
4. Contradictions between units, and the same hazard reported twice (list under "duplicates").
5. Blind spots: ways an ordinary account could take or lock other users' funds that no unit examined. Look at the list P1 to P8 in ASSUMPTIONS.md and ask which lever was never tried against which network feature. Look at the cleared items and ask which clearance rests on an assumption nobody tested.
Write leads as concrete questions a researcher can answer in one sitting. Mark "high" only those that could end in an in-scope critical or high finding.

${plan.done ? `A critic file from an earlier, partial run of this cycle exists at ${DIR}/critic.json. Read it first. Keep every lead, gap and duplicate in it that is still open, remove what the files written since then have settled, and add what those files show. The result replaces the old file.

` : ''}Output: write ${DIR}/critic.json in the "critic" format from SCHEMA.md. Run \`python3 ${ROOT}/tools/validate.py critic ${DIR}/critic.json\` until it prints OK. Return the summary object; "findings" is the number of leads, "inScope" the number marked high, and the headline is the most important lead.`,
  { label: 'critic', phase: 'Critic', schema: SUMMARY, ...MODEL })

return { cycle: plan.cycle, dir: DIR, units: done, dropped, critic }
