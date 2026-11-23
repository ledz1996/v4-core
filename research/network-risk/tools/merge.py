"""Fold one cycle directory into state/ and regenerate STATUS.md.

Usage: merge.py <cycle-dir> <YYYY-MM-DD>
Idempotent per cycle: running it twice for the same cycle is refused.
"""
import glob, json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
def load(p): return json.load(open(p))
def dump(p, o): json.dump(o, open(p, "w"), indent=1, ensure_ascii=False)
def main():
    cdir, date = sys.argv[1].rstrip("/"), sys.argv[2]
    cycle = int(os.path.basename(cdir))
    L = load(f"{R}/state/ledger.json"); FS = load(f"{R}/state/findings.json"); CL = load(f"{R}/state/cleared.json")
    if any(h["cycle"] == cycle for h in L["history"]): sys.exit(f"cycle {cycle} already merged")
    F = FS["findings"]; by_id = {f["id"]: f for f in F}
    next_f = 1 + max([int(f["id"][2:]) for f in F] or [0]); next_l = 1 + max([int(l["id"][2:]) for l in L["leads"]] or [0])
    known_q = {l["question"].strip().lower() for l in L["leads"]}
    stats = {"new": 0, "updated": 0, "confirmed": 0, "plausible": 0, "refuted": 0, "unverified": 0, "leads": 0, "leadsClosed": 0, "cleared": 0}
    def add_leads(items, origin):
        nonlocal next_l
        for l in items or []:
            q = l["question"].strip()
            if q.lower() in known_q: continue
            known_q.add(q.lower())
            L["leads"].append({"id": f"L-{next_l:03d}", "cycle": cycle, "origin": origin, "chainIds": l["chainIds"], "lens": l["lens"],
                               "question": q, "why": l["why"], "priority": l["priority"], "status": "open"})
            next_l += 1; stats["leads"] += 1
    # cycles/NNN/actors.json may classify findings written before the actor field existed: {"<unit>:<findingIndex>": "<actor>"}
    actors = load(f"{cdir}/actors.json") if os.path.exists(f"{cdir}/actors.json") else {}
    # cycles/NNN/skip.json drops findings the critic showed to be a second report of one event: {"<unit>:<findingIndex>": "<reason>"}
    skip = load(f"{cdir}/skip.json") if os.path.exists(f"{cdir}/skip.json") else {}
    # cycles/NNN/extends.json links a finding to an earlier one when the agent did not: {"<unit>:<findingIndex>": "F-xxx"}
    ext = load(f"{cdir}/extends.json") if os.path.exists(f"{cdir}/extends.json") else {}
    plan = load(f"{cdir}/plan.json") if os.path.exists(f"{cdir}/plan.json") else {}
    recheck = {u["id"]: set(u.get("recheckIds", [])) for u in plan.get("units", [])}
    units_done = []
    for rp in sorted(glob.glob(f"{cdir}/*.research.json")):
        res = load(rp); unit = res["unit"]; units_done.append(unit)
        vp = f"{cdir}/{unit}.verdicts.json"
        ver = {v["findingIndex"]: v for v in load(vp)["verdicts"]} if os.path.exists(vp) else {}
        for i, f in enumerate(res.get("findings", [])):
            if f"{unit}:{i}" in skip: stats["skipped"] = stats.get("skipped", 0) + 1; continue
            v = ver.get(i)
            status = v["verdict"] if v else "unverified"
            stats[status] += 1
            entry = {k: f[k] for k in ("title", "chainIds", "lens", "assumptions", "effect", "difference", "mechanism", "impact", "preconditions", "mitigations", "coreRefs", "sources", "evidence")}
            entry["actor"] = actors.get(f"{unit}:{i}", f.get("actor", "unclassified"))
            entry["severity"] = v["severity"] if v else f["severity"]
            entry["proposedSeverity"] = f["severity"]
            entry["status"] = status
            event = {"cycle": cycle, "unit": unit, "status": status, "severity": entry["severity"]}
            if v:
                entry["verification"] = {"cycle": cycle, "factCheck": v["factCheck"], "codeCheck": v["codeCheck"], "corrections": v.get("corrections", ""), "sources": v.get("sources", [])}
                entry["lastVerifiedCycle"] = cycle
            old = by_id.get(ext.get(f"{unit}:{i}", f.get("ref", "")))
            # Only a recheck that the plan assigned to this unit replaces the body of an existing finding.
            # Any other finding that names a "ref" adds to it (another network, another token) and is kept as its own entry.
            if old and old["id"] in recheck.get(unit, set()):
                hist = old.get("history", []) + [event]
                old.update(entry); old["history"] = hist; stats["updated"] += 1
            else:
                if old: entry["extends"] = old["id"]
                entry.update(id=f"F-{next_f:03d}", firstCycle=cycle, history=[event]); entry.setdefault("lastVerifiedCycle", 0)
                F.append(entry); by_id[entry["id"]] = entry; next_f += 1; stats["new"] += 1
        for c in res.get("cleared", []):
            CL["cleared"].append(dict(c, cycle=cycle, unit=unit)); stats["cleared"] += 1
        add_leads(res.get("leads"), unit)
        if os.path.exists(vp): add_leads(load(vp).get("leads"), unit + ":verifier")
        for r in res.get("leadResults", []):
            for l in L["leads"]:
                if l["id"] == r["leadId"] and l["status"] == "open":
                    if r["outcome"] != "inconclusive": l["status"] = "done"; stats["leadsClosed"] += 1
                    l.setdefault("attempts", []).append({"cycle": cycle, "outcome": r["outcome"], "answer": r["answer"]})
        if unit in L["units"]:
            covered = {(p["chainId"], p["lens"]) for p in res.get("profiles", [])}
            for (cid, lens) in covered:
                cell = L["cells"].get(f"{cid}:{lens}")
                if cell is None: continue
                cell["depth"] = min(3, cell["depth"] + (2 if os.path.exists(vp) and cell["depth"] == 0 else 1)); cell["lastCycle"] = cycle
    tp = f"{R}/state/themes.json"
    if os.path.exists(tp):
        T = load(tp)
        for t in T["themes"]:
            if t["status"] == "open" and t["id"] in units_done: t["status"] = "done"; t["cycle"] = cycle
        dump(tp, T)
    cp = f"{cdir}/critic.json"
    if os.path.exists(cp):
        c = load(cp); add_leads(c.get("leads"), "critic")
        L.setdefault("criticNotes", []).append({"cycle": cycle, "gaps": c.get("gaps", []), "duplicates": c.get("duplicates", [])})
        L["criticNotes"] = L["criticNotes"][-5:]
    # leads that survive three inconclusive attempts are parked so they stop crowding the queue
    for l in L["leads"]:
        if l["status"] == "open" and len(l.get("attempts", [])) >= 3: l["status"] = "parked"
    L["cycle"] = cycle
    L["history"].append(dict(stats, cycle=cycle, date=date, units=units_done))
    F.sort(key=lambda f: (f["status"] == "refuted", f.get("actor") != "unprivileged", ORDER[f["severity"]], f["id"]))
    dump(f"{R}/state/ledger.json", L); dump(f"{R}/state/findings.json", FS); dump(f"{R}/state/cleared.json", CL)
    print(json.dumps(stats))
    os.system(f"{sys.executable} {R}/tools/status.py")
main()
