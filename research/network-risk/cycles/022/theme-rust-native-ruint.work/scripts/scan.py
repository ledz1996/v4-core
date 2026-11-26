# List candidate ruint shift and signed-conversion sites in non-test code of the downloaded sources.
import os, re, sys, json
root = sys.argv[1]
SHIFT = re.compile(r'(?<![<>])(<<|>>)=?(?![>=])')
GEN = re.compile(r'(::<|<[A-Za-z_][\w:, &\']*>>)')
FN = re.compile(r'\b(overflowing_sh[lr]|checked_sh[lr]|wrapping_sh[lr]|saturating_sh[lr]|arithmetic_shr|unbounded_sh[lr]|rotate_(left|right)|\.sh[lr]\()')
CONV = re.compile(r'\b(wrapping_from|saturating_from|uint_try_from|try_from|try_into|checked_from|from_int|as_i\d+|I256|i256|Signed<|into_raw|unsigned_abs|into_sign_and_abs|from_dec_str|wrapping_to|saturating_to|\.to::<)')
out = {"shift": [], "fn": [], "conv": []}
for dp, dn, fs in os.walk(root):
    for f in fs:
        if not f.endswith('.rs'): continue
        p = os.path.join(dp, f)
        if re.search(r'/(tests?|benches|test_utils|testing)/', p) or f in ('tests.rs', 'test_utils.rs'): continue
        L = open(p, encoding='utf-8', errors='replace').read().split('\n')
        for i, l in enumerate(L):
            if re.match(r'\s*#\[cfg\(test\)\]', l) and i + 1 < len(L) and re.match(r'\s*(pub(\(\w+\))?\s+)?mod\s+\w+', L[i + 1]):
                break
            s = l.split('//')[0]
            if not s.strip(): continue
            rel = os.path.relpath(p, root) + ':' + str(i + 1)
            if SHIFT.search(GEN.sub('', s)) and not re.search(r'->\s|=>', s.replace('>>', '')):
                out["shift"].append(rel + '  ' + l.strip())
            elif SHIFT.search(GEN.sub('', s)):
                out["shift"].append(rel + '  ' + l.strip())
            if FN.search(s): out["fn"].append(rel + '  ' + l.strip())
            if CONV.search(s): out["conv"].append(rel + '  ' + l.strip())
json.dump(out, open(sys.argv[2], 'w'), indent=1)
for k, v in out.items(): print(k, len(v))
