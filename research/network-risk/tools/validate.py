"""Validate one cycle file. Usage: validate.py research|verdicts|critic <file>"""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEV = {"critical", "high", "medium", "low", "info"}
ACTORS = {"unprivileged", "pool-creator", "issuer", "operator", "governance"}
LENS = {"L1", "L2", "L3", "L4", "L5", "L6"}
errs = []
def need(o, k, t, where, allow_empty=False):
    if not isinstance(o, dict) or k not in o: errs.append(f"{where}: missing '{k}'"); return None
    v = o[k]
    if not isinstance(v, t): errs.append(f"{where}.{k}: wrong type"); return None
    if not allow_empty and t in (str, list) and len(v) == 0: errs.append(f"{where}.{k}: empty"); return None
    return v
def enum(o, k, vals, where):
    v = need(o, k, str, where)
    if v is not None and v not in vals: errs.append(f"{where}.{k}: '{v}' not in {sorted(vals)}")
def chain_ids(o, where, known):
    v = need(o, "chainIds", list, where) or []
    for c in v:
        if c not in known: errs.append(f"{where}.chainIds: unknown chainId {c}")
def sources(o, where):
    for i, s in enumerate(need(o, "sources", list, where) or []):
        u = need(s, "url", str, f"{where}.sources[{i}]"); need(s, "supports", str, f"{where}.sources[{i}]")
        if u and not u.startswith("http") and "rpc" not in u.lower() and ":" not in u: errs.append(f"{where}.sources[{i}].url: not a URL or on-chain reference")
def leads(d, known):
    for i, l in enumerate(d.get("leads", [])):
        w = f"leads[{i}]"; chain_ids(l, w, known); enum(l, "lens", LENS, w); need(l, "question", str, w); need(l, "why", str, w); enum(l, "priority", {"high", "medium", "low"}, w)
def main():
    kind, path = sys.argv[1], sys.argv[2]
    try: d = json.load(open(path))
    except Exception as e: print("INVALID JSON:", e); sys.exit(1)
    known = {n["chainId"] for n in json.load(open(f"{R}/state/networks.json"))["networks"]}
    ledger = json.load(open(f"{R}/state/ledger.json"))
    if kind == "research":
        unit = need(d, "unit", str, "root")
        if unit and unit not in ledger["units"] and not unit.startswith(("core-code", "theme-")): errs.append(f"unknown unit {unit}")
        seen = set()
        for i, p in enumerate(need(d, "profiles", list, "root", True) or []):
            w = f"profiles[{i}]"; cid = need(p, "chainId", int, w); enum(p, "lens", LENS, w); need(p, "summary", str, w)
            seen.add((cid, p.get("lens")))
            for j, x in enumerate(need(p, "deltas", list, w, True) or []):
                need(x, "delta", str, f"{w}.deltas[{j}]"); need(x, "source", str, f"{w}.deltas[{j}]"); enum(x, "relevance", {"none", "low", "high"}, f"{w}.deltas[{j}]")
        if unit in ledger["units"]:
            want = d.get("_lenses") or sorted(LENS)
            for cid in ledger["units"][unit]["chainIds"]:
                for l in want:
                    if (cid, l) not in seen: errs.append(f"profiles: no entry for chainId {cid} lens {l}")
        for i, f in enumerate(need(d, "findings", list, "root", True) or []):
            w = f"findings[{i}]"; need(f, "ref", str, w); need(f, "title", str, w); chain_ids(f, w, known); enum(f, "lens", LENS, w)
            need(f, "assumptions", list, w, True); enum(f, "effect", {"siphon", "freeze", "both", "degrade"}, w); enum(f, "severity", SEV, w)
            if "actor" in f or "/cycles/001/" not in os.path.abspath(path): enum(f, "actor", ACTORS, w)
            for k in ("difference", "mechanism", "impact", "preconditions", "mitigations"): need(f, k, str, w)
            need(f, "coreRefs", list, w); sources(f, w); enum(f, "evidence", {"primary", "secondary", "inferred"}, w)
        for i, c in enumerate(need(d, "cleared", list, "root", True) or []):
            w = f"cleared[{i}]"; chain_ids(c, w, known); enum(c, "lens", LENS, w); need(c, "check", str, w); need(c, "result", str, w); need(c, "source", str, w)
        leads(d, known)
        for i, r in enumerate(d.get("leadResults", [])):
            w = f"leadResults[{i}]"; need(r, "leadId", str, w); enum(r, "outcome", {"finding", "cleared", "inconclusive"}, w); need(r, "answer", str, w)
    elif kind == "verdicts":
        unit = need(d, "unit", str, "root")
        rp = os.path.join(os.path.dirname(path), f"{unit}.research.json")
        n = len(json.load(open(rp))["findings"]) if os.path.exists(rp) else None
        got = set()
        for i, v in enumerate(need(d, "verdicts", list, "root", True) or []):
            w = f"verdicts[{i}]"; idx = need(v, "findingIndex", int, w); got.add(idx)
            enum(v, "verdict", {"confirmed", "plausible", "refuted"}, w); enum(v, "severity", SEV, w)
            need(v, "factCheck", str, w); need(v, "codeCheck", str, w); need(v, "corrections", str, w, True); sources(v, w) if v.get("sources") else None
        if n is not None and got != set(range(n)): errs.append(f"verdicts: need exactly one verdict for each findingIndex 0..{n-1}, got {sorted(got)}")
        leads(d, known)
    elif kind == "critic":
        for i, g in enumerate(need(d, "gaps", list, "root", True) or []):
            chain_ids(g, f"gaps[{i}]", known); enum(g, "lens", LENS, f"gaps[{i}]"); need(g, "note", str, f"gaps[{i}]")
        need(d, "duplicates", list, "root", True); leads(d, known)
    else:
        errs.append("kind must be research, verdicts or critic")
    if errs:
        print("INVALID"); [print(" -", e) for e in errs[:60]]; sys.exit(1)
    print("OK")
main()
