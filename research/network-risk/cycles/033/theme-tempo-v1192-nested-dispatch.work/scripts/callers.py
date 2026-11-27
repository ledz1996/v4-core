#!/usr/bin/env python3
"""List call sites of nested-dispatch entry points in crawled Rust trees, tagging test code.
Usage: callers.py <root> [<root> ...]"""
import os, re, sys
PAT = re.compile(r'\.(transact|transact_with_inspector|call_tx|validate_tx|system_call|execute_system_call|system_call_with_inspector|committed_copy|transact_system_call|execute_tx|enter_execution|set_database|take_transient_storage|clear_transaction_state)\s*\(')
DEF = re.compile(r'fn\s+(transact|call_tx|system_call|execute_system_call|committed_copy|execute_tx|transact_system_call)\b')
for root in sys.argv[1:]:
    for dp, _, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith('.rs'): continue
            p = os.path.join(dp, f)
            lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
            testfile = '/tests/' in p or f in ('tests.rs', 'test_utils.rs') or '/test/' in p or 'test_util' in p or '/e2e/' in p
            test_from = None
            for i, l in enumerate(lines):
                if re.match(r'\s*#\[cfg\(test\)\]', l):
                    for j in range(i+1, min(i+3, len(lines))):
                        if re.match(r'\s*(pub(\(\w+\))?\s+)?mod\s+\w+\s*\{', lines[j]):
                            test_from = i if test_from is None else min(test_from, i)
                            break
            for i, l in enumerate(lines):
                s = l.strip()
                if s.startswith('//'): continue
                m = PAT.search(l) or DEF.search(l)
                if not m: continue
                tag = 'TEST' if testfile or (test_from is not None and i >= test_from) else 'PROD'
                print(f"{tag}\t{p}:{i+1}\t{s[:160]}")
