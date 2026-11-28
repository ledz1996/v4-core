"""For every depth decrement that classify.py accepted, the comparison that guards it (cmp BYTE PTR [..],K followed by
jae/jb to the revert side): K-1 must be the last success code of the binary's InstructionResult. Reads only."""
import json, re, subprocess, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bins import BINS
prof, clsf = sys.argv[1:3]
P = BINS[prof]; d = json.load(open(clsf)); cnt = collections.Counter(); ex = {}
for x in d['decrements']:
    if not x['ok']: continue
    a = int(x['addr'], 16)
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % (a - 0x18),
                          '--stop-address=%#x' % a, P['bin']], capture_output=True, text=True).stdout
    L = [re.sub(r'\s*<[^>]*>', '', l.split(':', 1)[1]).strip() for l in out.splitlines() if re.match(r'^\s*[0-9a-f]+:\s', l)]
    k = None
    for i in range(len(L) - 1):
        m = re.match(r'^cmp\s+BYTE PTR \[.*\],(0x[0-9a-f]+)$', L[i])
        if m and re.match(r'^(jae|jb|ja|jbe)\s', L[i + 1]): k = (L[i + 1].split()[0], int(m.group(1), 16))
    cnt[k] += 1; ex.setdefault(str(k), x['addr'])
print(prof, dict(cnt), ex)
