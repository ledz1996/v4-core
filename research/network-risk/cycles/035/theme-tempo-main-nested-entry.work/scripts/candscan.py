#!/usr/bin/env python3
"""For each candidate ref (out/candidate_refs.txt), list relevant .rs files that differ from main
(tree-only diff), batch-fetch their blobs, and report nested-dispatch call sites whose text is not
present in main's copy of the same file. Usage: candscan.py"""
import os, re, subprocess, sys, json
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(W, 'dl', 'tempo.git')
MAIN = '0fe724b50121a0d82c4594d2bec225ae42a57fb2'
PATHS = ['crates/precompiles', 'crates/evm', 'crates/payload', 'crates/zones/precompiles', 'crates/zones/evm', 'crates/primitives', 'crates/revm', 'crates/node/src']
PAT = re.compile(r'\.(transact\w*\(|inspect_tx\w*\(|call_tx\(|system_call\w*\(|execute_system_call\(|committed_copy\(|execute_tx\(|enter_execution\(|set_database\(|take_transient_storage\(|clear_transaction_state\(|clear_pending_state\(|commit_transaction\(|transient_storage_mut\(|execute_message\(|execute_call\()|fn (transact|call_tx|system_call|execute_system_call|committed_copy|execute_tx)\b|TxEnv\s*\{|TxEnv::<')
env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
def git(*a, check=True):
    return subprocess.run(['git', '-C', G] + list(a), capture_output=True, text=True, env=env, check=check).stdout
refs = [l.split() for l in open(os.path.join(W, 'out', 'candidate_refs.txt'))]
changed = {}
need = set()
for sha, ref in refs:
    out = git('diff', '--name-status', '--no-renames', MAIN, sha, '--', *PATHS)
    files = []
    for l in out.splitlines():
        st, p = l.split('\t', 1)
        if not p.endswith('.rs') or st == 'D': continue
        files.append(p)
    changed[(sha, ref)] = files
for (sha, ref), files in changed.items():
    for p in files:
        o = git('rev-parse', f'{sha}:{p}', check=False).strip()
        if o: need.add(o)
for p in set(p for fs in changed.values() for p in fs):
    o = git('rev-parse', f'{MAIN}:{p}', check=False).strip()
    if o: need.add(o)
have = set()
r = subprocess.run(['git', '-C', G, 'rev-list', '--objects', '--missing=print', '--no-walk=unsorted', MAIN] + sorted(set(s for s, _ in refs)), capture_output=True, text=True, env=env)
missing = set(l[1:] for l in r.stdout.splitlines() if l.startswith('?'))
want = sorted(need & missing)
print('blobs needed', len(need), 'missing', len(want), file=sys.stderr)
for i in range(0, len(want), 400):
    subprocess.run(['git', '-C', G, '-c', 'fetch.negotiationAlgorithm=noop', 'fetch', '-q', '--no-tags', '--no-write-fetch-head', '--filter=blob:none', 'origin'] + want[i:i+400], check=True)
def sites(txt):
    s = set(); lines = txt.split('\n')
    test_from = None
    for i, l in enumerate(lines):
        if re.match(r'\s*#\[cfg\(test\)\]', l) and i + 1 < len(lines) and re.match(r'\s*(pub(\(\w+\))?\s+)?mod\s+\w+', lines[i+1]):
            test_from = i; break
    for i, l in enumerate(lines):
        if l.strip().startswith('//'): continue
        if test_from is not None and i >= test_from: continue
        if PAT.search(l): s.add(l.strip())
    return s
bp = subprocess.Popen(['git', '-C', G, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
def blob(spec):
    bp.stdin.write((spec + '\n').encode()); bp.stdin.flush()
    h = bp.stdout.readline().decode().split()
    if len(h) < 3 or h[1] == 'missing': return ''
    d = bp.stdout.read(int(h[2])); bp.stdout.read(1)
    return d.decode('utf-8', 'replace')
report = {}
for (sha, ref), files in changed.items():
    new = []
    for p in files:
        if '/tests/' in p or p.endswith('tests.rs') or '/benches/' in p or 'test_util' in p: continue
        cand = blob(f'{sha}:{p}')
        base = blob(f'{MAIN}:{p}')
        for t in sorted(sites(cand) - sites(base)):
            new.append(f'{p}: {t[:200]}')
    report[ref] = {'sha': sha, 'changed_relevant_rs': len(files), 'new_call_sites': new}
json.dump(report, open(os.path.join(W, 'out', 'candscan.json'), 'w'), indent=1)
n = sum(1 for v in report.values() if v['new_call_sites'])
print('refs', len(report), 'with relevant changes', sum(1 for v in report.values() if v['changed_relevant_rs']), 'with new call sites', n)
