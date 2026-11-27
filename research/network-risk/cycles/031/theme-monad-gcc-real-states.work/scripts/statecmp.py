"""Cycle 31: compare two state logs of the hook (clang build and system gcc build) with the element pointers renamed
to their order of first appearance per log line. usage: statecmp.py a.jsonl b.jsonl"""
import sys, json, re
def canon(l):
    ids = {}
    def sub(m):
        p = m.group(0)
        if p == '"(nil)"': return p
        ids.setdefault(p, len(ids)); return '"P%d"' % ids[p]
    return re.sub(r'"(0x[0-9a-f]+|\(nil\))"', sub, l)
A = open(sys.argv[1]).read().splitlines(); B = open(sys.argv[2]).read().splitlines()
diff = [i for i, (a, b) in enumerate(zip(A, B)) if canon(a) != canon(b)]
print('lines', len(A), len(B), 'differing after pointer renaming', len(diff) + abs(len(A) - len(B)), diff[:5])
