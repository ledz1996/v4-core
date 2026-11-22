"""Render STATUS.md from state/. Deterministic; no prose is generated here."""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(f"{R}/state/ledger.json")); F = json.load(open(f"{R}/state/findings.json"))["findings"]
N = {n["chainId"]: n for n in json.load(open(f"{R}/state/networks.json"))["networks"]}
lenses = sorted(L["lenses"])
out = ["# Network risk ledger", "", f"Cycle {L['cycle']}. {len(N)} networks, {len(F)} findings on record, "
       f"{sum(1 for l in L['leads'] if l['status']=='open')} open leads.", ""]
out += ["## Findings", "", "| ID | Severity | Status | Effect | Networks | Title |", "|---|---|---|---|---|---|"]
for f in F:
    nets = ", ".join(N[c]["name"] for c in f["chainIds"]) if len(f["chainIds"]) < len(N) else "all 21"
    out.append(f"| {f['id']} | {f['severity']} | {f['status']} | {f['effect']} | {nets} | {f['title']} |")
out += ["", "## Coverage", "", "Each cell is depth/last cycle. Depth 0 is untouched, 1 surveyed, 2 surveyed and independently checked, 3 revisited.", "",
        "| Network | Chain ID | " + " | ".join(lenses) + " |", "|---|---|" + "---|" * len(lenses)]
for uid, u in L["units"].items():
    for cid in u["chainIds"]:
        out.append(f"| {N[cid]['name']} | {cid} | " + " | ".join(f"{L['cells'][f'{cid}:{l}']['depth']}/{L['cells'][f'{cid}:{l}']['lastCycle']}" for l in lenses) + " |")
out += ["", "Lenses:", ""] + [f"- {k}: {v}" for k, v in L["lenses"].items()]
out += ["", "## Open leads", "", "| ID | Priority | Networks | Lens | Question |", "|---|---|---|---|---|"]
pr = {"high": 0, "medium": 1, "low": 2}
for l in sorted([l for l in L["leads"] if l["status"] == "open"], key=lambda l: (pr[l["priority"]], l["id"])):
    out.append(f"| {l['id']} | {l['priority']} | {', '.join(N[c]['name'] for c in l['chainIds'][:4])}{' …' if len(l['chainIds'])>4 else ''} | {l['lens']} | {l['question'].replace('|','/')} |")
out += ["", "## Cycle history", "", "| Cycle | Date | Units | New | Updated | Confirmed | Plausible | Refuted | Leads opened | Leads closed |", "|---|---|---|---|---|---|---|---|---|---|"]
for h in L["history"]:
    out.append(f"| {h['cycle']} | {h['date']} | {len(h['units'])} | {h['new']} | {h['updated']} | {h['confirmed']} | {h['plausible']} | {h['refuted']} | {h['leads']} | {h['leadsClosed']} |")
open(f"{R}/STATUS.md", "w").write("\n".join(out) + "\n")
print("STATUS.md written")
