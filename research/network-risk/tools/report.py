"""Render REPORT.md, FINDINGS.md and CLEARED.md from state/ and report/front.md.

report/front.md is written by hand each cycle (the answer so far, what was tested, what is open).
Everything below it is generated, so the report never drifts from the ledger.
"""
import json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(f"{R}/state/ledger.json")); F = json.load(open(f"{R}/state/findings.json"))["findings"]
C = json.load(open(f"{R}/state/cleared.json"))["cleared"]
NL = json.load(open(f"{R}/state/networks.json"))["networks"]; N = {n["chainId"]: n for n in NL}
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
ACTOR = {"unprivileged": "any account", "pool-creator": "author of a hook or token the victims use", "issuer": "token issuer or admin",
         "operator": "sequencer, validator or bridge committee", "governance": "owner, fee controller or chain governance", "unclassified": "not classified"}
def nets(ids):
    return "all 21 networks" if len(set(ids)) >= len(N) else ", ".join(N[c]["name"] for c in ids)
def card(f, level="###"):
    v = f.get("verification", {})
    out = [f"{level} {f['id']}. {f['title']}", "",
           f"{f['severity'].capitalize()} severity, {f['status']}. Effect: {f['effect']}. Who can trigger it: {ACTOR[f.get('actor', 'unclassified')]}. Networks: {nets(f['chainIds'])}.", "",
           f"What differs on the network: {f['difference']}", "", f"How it meets the code: {f['mechanism']}", "",
           f"What is at risk: {f['impact']}", "", f"What it takes: {f['preconditions']}", "", f"What can be done: {f['mitigations']}", ""]
    if f.get("extends"): out += [f"This entry adds to {f['extends']}.", ""]
    if v.get("corrections"): out += [f"Second reviewer's corrections: {v['corrections']}", ""]
    out += ["Code: " + ", ".join(f"`{r}`" for r in f["coreRefs"]) + ".", ""]
    out += ["Sources:", ""] + [f"- {s['url']} ({s['supports']})" for s in f["sources"]] + [""]
    return out
live = [f for f in F if f["status"] != "refuted"]
key = lambda f: (ORDER[f["severity"]], f["id"])
inscope = sorted([f for f in live if f.get("actor") == "unprivileged"], key=key)
rest = sorted([f for f in live if f.get("actor") != "unprivileged"], key=lambda f: (list(ACTOR).index(f.get("actor", "unclassified")), ) + key(f))
refuted = [f for f in F if f["status"] == "refuted"]
out = [open(f"{R}/report/front.md").read().rstrip(), ""]
out += ["## Findings an ordinary account can trigger", ""]
if not inscope: out += ["None on record.", ""]
for f in inscope: out += card(f)
out += ["## Findings that need a privileged party", "",
        "These are outside the threat model and are listed for reference. Full text is in `FINDINGS.md`.", "",
        "| ID | Needs | Severity | Status | Networks | Finding |", "|---|---|---|---|---|---|"]
for f in rest:
    out.append(f"| {f['id']} | {ACTOR[f.get('actor', 'unclassified')]} | {f['severity']} | {f['status']} | {nets(f['chainIds'])} | {f['title']} |")
if refuted:
    out += ["", "## Refuted", "", "| ID | Networks | Claim | Why it fails |", "|---|---|---|---|"]
    for f in refuted: out.append(f"| {f['id']} | {nets(f['chainIds'])} | {f['title']} | {f.get('verification', {}).get('corrections', '').replace('|', '/')[:400]} |")
out += ["", "## The 21 networks as read from chain", "",
        "| Network | Chain ID | PoolManager | Code size | Code group | Block gas limit | Fee controller set |", "|---|---|---|---|---|---|---|"]
groups = {}
for n in NL: groups.setdefault(n.get("maskedSha256"), len(groups) + 1)
for n in NL:
    out.append(f"| {n['name']} | {n['chainId']} | `{n['poolManager']}` | {n.get('codeLen')} | {chr(64 + groups[n.get('maskedSha256')])} | {n.get('blockGasLimit'):,} | {'yes' if int(n.get('protocolFeeController', '0x0'), 16) else 'no'} |")
out += ["", "Code group compares the deployed bytecode after blanking the contract's own address. Networks in the same group run the same code.", "",
        "## Where the evidence is", "",
        "- `FINDINGS.md`: every finding in full, including the out-of-scope ones.",
        f"- `CLEARED.md`: the {len(C)} checks that came out safe, with the reason for each.",
        "- `STATUS.md`: coverage per network and lens, open leads, cycle history.",
        "- `cycles/NNN/`: the raw research and verdict files of each cycle.", ""]
open(f"{R}/REPORT.md", "w").write("\n".join(out))
allc = ["# All findings", "", f"{len(F)} findings on record after cycle {L['cycle']}, in-scope ones first.", ""]
for f in inscope + rest + refuted: allc += card(f, "##")
open(f"{R}/FINDINGS.md", "w").write("\n".join(allc))
cl = ["# Checks that came out safe", "", f"{len(C)} checks after cycle {L['cycle']}. Each entry gives what was tested, why it is safe, and the evidence.", ""]
by = {}
for c in C: by.setdefault(c["unit"], []).append(c)
for unit, items in by.items():
    title = L["units"].get(unit, {}).get("title", "Reading of the source (" + unit.replace("core-code-", "") + ")")
    cl += [f"## {title}", ""]
    for c in items:
        cl += [f"- {nets(c['chainIds'])}, cycle {c['cycle']}. {c['check'].rstrip('.')}. Result: {c['result']} Evidence: {c['source']}"]
    cl += [""]
open(f"{R}/CLEARED.md", "w").write("\n".join(cl))
# prose lint: patterns the style guide rules out. Reported, never auto-fixed.
bad = re.compile(r"[—–]|\b(crucial|robust|landscape|pivotal|delve|testament|seamless|leverag\w+)\b", re.I)
hits = [(name, m.group(0)) for name in ("REPORT.md",) for m in bad.finditer(open(f"{R}/{name}").read())]
print(f"REPORT.md: {len(inscope)} in-scope cards, {len(rest)} out-of-scope rows; FINDINGS.md and CLEARED.md written; lint hits: {len(hits)} {hits[:8]}")
