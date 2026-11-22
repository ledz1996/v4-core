export const meta = {
  name: 'v4-network-risk-cycle',
  description: 'One cycle of the v4-core network risk review: research per network family, independent verification, gap critic',
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
    headline: { type: 'string' },
  },
  required: ['file', 'validated', 'findings', 'headline'],
}

const COMMON = `
You are part of a defensive security review. The repository at /home/user/v4-core holds the Solidity source of a Uniswap v4 style PoolManager. This build is a CTF variant that will be deployed to 21 EVM networks, and the organisers say at least one path exists that freezes or siphons pool funds. The review must find every such path so they can be closed before deployment. Analysis only: do not write exploit code or proof-of-concept contracts, and do not send transactions. Read-only JSON-RPC calls (eth_call, eth_getCode, eth_getStorageAt, eth_getBlockByNumber) are fine.

Ground rules
- Read the code in this repository as it is written. Treat every line as unreviewed. Do not rely on what you remember about Uniswap v4, and never diff or compare this code against upstream v4-core or any other copy. The owner of this review has forbidden that. Judge behaviour from the text in src/ and lib/.
- What counts: anything that lets someone take funds held by the PoolManager (pool reserves, ERC-6909 claims, protocol fees), or stops LPs and swappers from getting their funds out. Griefing and pure MEV do not count unless they end in loss or a freeze.
- Evidence: every chain fact needs a source URL you actually fetched in this session (official docs, specs, improvement proposals, client source, block explorers) or an on-chain query you ran. Every code claim needs a file:line in this repo that you read. Never invent a URL. If something may postdate your training data, look it up. If you could not confirm a link in the chain of reasoning, say which one.
- Tools: load web tools with ToolSearch (query "select:WebSearch,mcp__Exa__web_search_exa,mcp__Exa__web_fetch_exa"). curl works for public RPC endpoints, docs sites and raw.githubusercontent.com. The GitHub API and git clone of other repositories are not available.
- Do not edit anything outside ${DIR}/. Do not run git commands that change state. Do not create extra notes or planning files.
- Shared context to read first: ${ROOT}/ASSUMPTIONS.md (what the code assumes about the chain, A1 to A14, with line numbers), ${ROOT}/SCHEMA.md (output format, severity scale, prose style), ${ROOT}/state/networks.json (the 21 networks with PoolManager address, a working RPC URL, block gas limit, owner and fee controller read from chain), ${ROOT}/state/findings.json and ${ROOT}/state/cleared.json (what earlier cycles already established; extend or correct those by id, do not repeat them).
`

function researchPrompt(u) {
  const leads = u.leadIds && u.leadIds.length ? `Open leads assigned to you (look them up by id in ${ROOT}/state/ledger.json and answer each in "leadResults"): ${u.leadIds.join(', ')}.` : ''
  const recheck = u.recheckIds && u.recheckIds.length ? `Findings still unsettled for your networks (settle them: re-report with "ref" set to the id and better evidence, or explain in "cleared" why they fail): ${u.recheckIds.join(', ')}.` : ''
  return `${COMMON}
Your unit: "${u.id}" (${u.title}). Chain IDs: ${u.chainIds.join(', ')}. Mode: ${u.mode}. Lenses to cover for every chain in the unit: ${u.lenses.join(', ')} (definitions are in ${ROOT}/state/ledger.json under "lenses").
Angle for this cycle: ${u.angle}
${leads}
${recheck}

Method
1. For each network, establish how it differs from Ethereum mainnet at the protocol level under each lens. Start from the network's own technical docs and specs, then client source where the docs are vague. Use the RPC URL in networks.json to check anything that can be read from chain (code at system addresses, token behaviour, block fields).
2. For each difference, open the code path in src/ that would meet it and decide: hazard, cleared, or lead for a later cycle. ASSUMPTIONS.md lists the code paths; read the actual lines before you cite them.
3. Think about the assets pools will hold on this network: the gas token, its wrapped or ERC-20 form, tokens built into the protocol, and issuer-controlled assets the chain treats specially. Ask what a holder, the issuer and the chain itself can each do to the balance at the PoolManager address.
4. Walk the four fund-moving entry points through each difference: sync, settle and settleFor, take, and collectProtocolFees. Then unlock and the hook calls.
5. Prefer a few well-supported findings to many thin ones. Put differences you checked and found safe in "cleared" with the reason, so later cycles do not redo them. Put open questions you could not close in "leads".

Output: write ${DIR}/${u.id}.research.json in the "research" format from SCHEMA.md, with "unit": "${u.id}"${u.mode === 'baseline' ? '' : ` and "_lenses": ${JSON.stringify(u.lenses)}`}. Include one "profiles" entry for every (chainId, lens) pair assigned. Run \`python3 ${ROOT}/tools/validate.py research ${DIR}/${u.id}.research.json\` and fix the file until it prints OK. Then return the summary object: the file path, whether validation passed, the number of findings, and one sentence naming your most serious finding (or saying there is none).`
}

function codePrompt(c) {
  return `${COMMON}
Your unit: "${c.id}". You read the source itself, line by line, looking for any path to siphoning or freezing funds that exists in the code as written, on any of the 21 networks or on all of them.
Files: ${c.files}.

Method
1. Read every line of the files above, including assembly blocks, constants, masks, slot derivations, casts, unchecked blocks and comparison operators. For each function write down (for yourself) what it must guarantee, then check the text guarantees it. Pay attention to: sign and direction of every delta, rounding direction in each math step, which caller is credited or debited, slot constants and whether two of them could collide, masks and shifts, bounds on ticks, prices, fees and liquidity, access control on every external function, the order of state updates around external calls, and what happens on the error paths.
2. Check constants against their stated derivations by computing them (python3 or cast keccak if available): transient slot constants, hook flag bits, tick and price bounds, fee maxima, magic numbers in TickMath and BitMath.
3. The tests in test/ show intended behaviour. Use them to learn intent, and note any place where the source and the tests disagree. You may run \`forge build\` or \`forge test\` if forge is installed; do not install anything.
4. For anything suspicious, work out by hand whether it lets someone take funds or lock them, and on which networks. Tie it to a network property when one is needed (see ASSUMPTIONS.md and networks.json).
5. Report only what the text supports. A function that looks unusual but is safe goes in "cleared" with the reason.

Output: write ${DIR}/${c.id}.research.json in the "research" format from SCHEMA.md, with "unit": "${c.id}" and "profiles": []. Use "chainIds" for the networks affected (all 21 chain IDs from networks.json when the issue is chain independent), lens "L1" for pure code issues unless another fits better, and "sources" entries of the form {"url": "src/File.sol:line", "supports": "..."} when the evidence is the code itself. Run \`python3 ${ROOT}/tools/validate.py research ${DIR}/${c.id}.research.json\` until it prints OK. Then return the summary object.`
}

function verifyPrompt(id) {
  return `${COMMON}
You are the independent verifier for unit "${id}". Another agent wrote ${DIR}/${id}.research.json. Your job is to try to break each of its findings. You have no stake in them being right.

For every entry in "findings":
1. Fact check. Fetch the cited sources and read what they actually say. Look for a primary source that contradicts the claim. Where the claim can be tested on chain, run the read-only query against the RPC URL in networks.json.
2. Code check. Open the cited lines in src/ and trace the path yourself. Look for a guard the finding missed (for example the msg.value check in _settle, the unlocked-and-synced check in collectProtocolFees, the delta count check at the end of unlock, return data length checks in Hooks). Check whether the tests in test/ cover the case.
3. Severity. Apply the scale in SCHEMA.md. Who has to act, what do they need, and which funds are reachable? Lower or raise the severity accordingly.
4. Verdict: "confirmed" only when both the chain fact and the code path hold up under your own reading. "plausible" when the mechanism is sound but a link is unconfirmed; say which. "refuted" when a primary source or the code contradicts it; say what.
Then spot-check the three "cleared" items where a mistake would cost the most, and record whether you agree. If your checking turns up a hazard the researcher missed, add it to "leads".

Output: write ${DIR}/${id}.verdicts.json in the "verdicts" format from SCHEMA.md with "unit": "${id}" and one verdict per finding index. If the research file has no findings, write an empty "verdicts" array and still do the spot checks. Run \`python3 ${ROOT}/tools/validate.py verdicts ${DIR}/${id}.verdicts.json\` until it prints OK. Return the summary object; "findings" is the number you confirmed and the headline names the strongest confirmed finding or says none survived.`
}

const jobs = [
  ...plan.units.map(u => ({ id: u.id, prompt: researchPrompt(u) })),
  ...plan.code.map(c => ({ id: c.id, prompt: codePrompt(c) })),
]
log(`Cycle ${plan.cycle}: ${plan.units.length} network units, ${plan.code.length} source readers, each followed by a verifier, then one critic (${jobs.length * 2 + 1} agents)`)

const results = await pipeline(
  jobs,
  j => agent(j.prompt, { label: `research:${j.id}`, phase: 'Research', schema: SUMMARY }),
  (r, j) => agent(verifyPrompt(j.id), { label: `verify:${j.id}`, phase: 'Verify', schema: SUMMARY })
    .then(v => ({ id: j.id, research: r, verify: v })),
)

const done = results.filter(Boolean)
const dropped = jobs.filter(j => !done.find(d => d.id === j.id)).map(j => j.id)
if (dropped.length) log(`Units that did not finish and are not covered this cycle: ${dropped.join(', ')}`)

phase('Critic')
const critic = await agent(`${COMMON}
You are the completeness critic for cycle ${plan.cycle}. Read every *.research.json and *.verdicts.json in ${DIR}/, plus ${ROOT}/state/ledger.json.
Units that failed to produce output this cycle: ${dropped.length ? dropped.join(', ') : 'none'}.

Produce the work list for the next cycle:
1. Gaps: (chainId, lens) pairs whose profile is thin, rests on secondary sources, or skipped a difference you know of or can find quickly.
2. Transfer: a hazard confirmed on one network that probably applies to another network where nobody checked. Name both.
3. Unsettled: findings left "plausible", and the single fact that would settle each.
4. Contradictions between units, and findings that are the same hazard reported twice (list under "duplicates").
5. Blind spots: classes of fund freeze or siphon that no unit looked at this cycle. Think about what the code trusts (ASSUMPTIONS.md) and which of those trusts nobody tested on which network.
Write leads as concrete questions a researcher can answer in one sitting. Mark as "high" only those that could end in a critical or high finding.

Output: write ${DIR}/critic.json in the "critic" format from SCHEMA.md. Run \`python3 ${ROOT}/tools/validate.py critic ${DIR}/critic.json\` until it prints OK. Return the summary object; "findings" is the number of leads and the headline is the most important lead.`,
  { label: 'critic', phase: 'Critic', schema: SUMMARY })

return { cycle: plan.cycle, dir: DIR, units: done, dropped, critic }
