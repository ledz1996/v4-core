#!/usr/bin/env python3
"""Mirror the Rust sources of a GitHub repository at a fixed ref through raw.githubusercontent.com.

There is no directory listing, so the crawler starts at each crate's lib.rs / main.rs (and build.rs)
and follows `mod name;` declarations (with #[path] attributes), the Rust module rules for
foo.rs / foo/mod.rs / parent/foo.rs, and `include!`/`include_str!` of .rs files.
Usage: crawl.py <owner/repo> <ref> <outdir> <crate_dir> [<crate_dir> ...]
"""
import os, re, subprocess, sys, urllib.request

owner_repo, ref, out = sys.argv[1], sys.argv[2], sys.argv[3]
crates = sys.argv[4:]
BASE = f"https://raw.githubusercontent.com/{owner_repo}/{ref}/"
seen = {}
log = open(os.path.join(out, "crawl.log"), "a")


def fetch(path):
    if path in seen:
        return seen[path]
    dst = os.path.join(out, path)
    if os.path.exists(dst):
        seen[path] = open(dst, encoding="utf-8", errors="replace").read()
        return seen[path]
    try:
        r = subprocess.run(["curl", "-sS", "-f", "-o", "-", BASE + path], capture_output=True, timeout=60)
        if r.returncode != 0:
            seen[path] = None
            log.write(f"404 {path}\n")
            return None
        txt = r.stdout.decode("utf-8", "replace")
    except Exception as e:
        seen[path] = None
        log.write(f"ERR {path} {e}\n")
        return None
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(txt)
    log.write(f"200 {path}\n")
    seen[path] = txt
    return txt

MOD_RE = re.compile(r'(?:#\[path\s*=\s*"([^"]+)"\]\s*(?:#\[[^\]]*\]\s*)*)?(?:pub(?:\([^)]*\))?\s+)?mod\s+(r#)?(\w+)\s*;')
CFGPATH_RE = re.compile(r'#\[cfg_attr\([^\]]*path\s*=\s*"([^"]+)"\)\]\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;')
INCL_RE = re.compile(r'include!\(\s*"([^"]+\.rs)"\s*\)')


def strip_comments(t):
    t = re.sub(r'//[^\n]*', '', t)
    return t


def visit(path, is_root_or_modrs):
    txt = fetch(path)
    if txt is None:
        return False
    d = os.path.dirname(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    moddir = d if is_root_or_modrs else os.path.join(d, stem)
    body = strip_comments(txt)
    for m in MOD_RE.finditer(body):
        explicit, _, name = m.group(1), m.group(2), m.group(3)
        if explicit:
            p = os.path.normpath(os.path.join(d, explicit))
            visit(p, explicit.endswith("mod.rs"))
            continue
        a = os.path.join(moddir, name + ".rs")
        if not visit(a, False):
            visit(os.path.join(moddir, name, "mod.rs"), True)
    for m in CFGPATH_RE.finditer(body):
        visit(os.path.normpath(os.path.join(d, m.group(1))), False)
    for m in INCL_RE.finditer(body):
        visit(os.path.normpath(os.path.join(d, m.group(1))), False)
    return True

for c in crates:
    fetch(os.path.join(c, "Cargo.toml"))
    for root in ("src/lib.rs", "src/main.rs", "build.rs"):
        visit(os.path.join(c, root), True)
    # bin targets
    for b in ("src/bin/main.rs",):
        visit(os.path.join(c, b), True)
print(sum(1 for v in seen.values() if v is not None), "files")
