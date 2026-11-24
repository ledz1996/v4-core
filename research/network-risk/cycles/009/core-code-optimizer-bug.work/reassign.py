"""For each Yul function whose load count changed in the LoadResolver step, list the variables that are reassigned (assignment without let),
and the variables that flow from them through let definitions; then list the memory and storage operations whose address uses any of them."""
import re, sys, json
sys.path.insert(0, '.')
from loadcount import strip, funcs, obj
t = strip(open(sys.argv[1]).read()); rt = obj(t, 'PoolManager_1216_deployed')
F = funcs(rt); ch = json.load(open(sys.argv[2]))['runtime']['changed_functions']
out = {}
for f in ch:
    body = F[f]
    stm = [s.strip() for s in re.split(r'\n', body) if s.strip()]
    reas = set()
    for s in stm:
        m = re.match(r'^([\w\s,]+?)\s*:=', s)
        if m and not s.startswith('let '):
            for v in m.group(1).split(','): reas.add(v.strip())
    # taint through let x := expr containing tainted vars (one forward pass, repeated)
    taint = set(reas)
    for _ in range(5):
        for s in stm:
            m = re.match(r'^let ([\w\s,]+?)\s*:=\s*(.*)$', s) or re.match(r'^([\w\s,]+?)\s*:=\s*(.*)$', s)
            if m:
                rhs = m.group(2); names = set(re.findall(r'\b[A-Za-z_][\w]*\b', rhs))
                if names & taint:
                    for v in m.group(1).split(','): taint.add(v.strip())
    hits = []
    for s in stm:
        for op in ['mload', 'sload', 'mstore', 'sstore', 'keccak256']:
            for mm in re.finditer(r'\b' + op + r'\(', s):
                # first argument
                i = mm.end(); d = 1; j = i
                while d:
                    if s[j] == '(': d += 1
                    elif s[j] == ')': d -= 1
                    elif s[j] == ',' and d == 1: break
                    j += 1
                arg = s[i:j]
                if set(re.findall(r'\b[A-Za-z_]\w*\b', arg)) & taint: hits.append(s[:160])
    out[f] = {'reassigned': sorted(reas), 'tainted_count': len(taint), 'ops_with_tainted_address': hits}
json.dump(out, open(sys.argv[3], 'w'), indent=1)
for f, v in out.items(): print(f, v['reassigned'], len(v['ops_with_tainted_address'])); [print('    ', h) for h in v['ops_with_tainted_address'][:12]]
