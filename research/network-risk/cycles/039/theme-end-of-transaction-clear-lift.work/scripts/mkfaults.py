"""Cycle 39 Task 5: plant faults in in-memory copies (the model's instruction table only) of every end-of-transaction
# (celo1010:1d66c80 depth_kept and txid_kept: the one 16-byte store 0x1d66fe6 that zeroes depth and id together, removed by hand)
routine in units.py, found in its objdump text: transient map kept (the branch that skips the clear taken always),
journal kept (the store of zero to the journal length removed), depth left raised (zero store to depth removed),
id not advanced (the store of the new id removed), logs kept (zero store to the logs length removed).
usage: python3 -I mkfaults.py <out.json>"""
import json, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
from units import UNITS
from bins import BINS
F = {}
for prof, kind, fn in UNITS:
    fr = None
    for l in open(BINS[prof]['fde']):
        a, b = (int(x, 16) for x in re.split(r'\.\.+', l.strip()))
        if a == fn: fr = (a, b); break
    t = subprocess.run(['objdump', '-d', '-M', 'intel', '--no-show-raw-insn', '--start-address=%#x' % fr[0], '--stop-address=%#x' % fr[1], BINS[prof]['bin']], capture_output=True, text=True).stdout
    L = [(int(m.group(1), 16), re.sub(r'\s*<[^>]*>', '', m.group(2)).split('#')[0].strip()) for l in t.splitlines() for m in [re.match(r'^\s*([0-9a-f]+):\s+(.*)$', l)] if m]
    f = {}
    for i, (x, s) in enumerate(L):
        if re.search(r'PTR \[\w+\+0x108\]', s) and 'transient_kept' not in f:
            for y, s2 in L[i + 1:i + 4]:
                m = re.match(r'^je\s+([0-9a-f]+)$', s2)
                if m: f['transient_kept'] = {'%x' % y: 'jmp    ' + m.group(1)}; break
        if re.match(r'^mov\s+QWORD PTR \[\w+\+0x28\],0x0$', s) and 'journal_kept' not in f: f['journal_kept'] = {'%x' % x: 'nop'}
        if re.match(r'^mov\s+QWORD PTR \[\w+\+0x118\],0x0$', s): f['depth_kept'] = {'%x' % x: 'nop'}
        if re.match(r'^(mov\s+DWORD PTR \[\w+\+0x120\],e\w+|inc\s+QWORD PTR \[\w+\+0x120\]|add\s+QWORD PTR \[\w+\+0x120\],0x1|mov\s+QWORD PTR \[\w+\+0x120\],0x0)$', s): f['txid_kept'] = {'%x' % x: 'nop'}
        if re.match(r'^mov\s+QWORD PTR \[\w+\+0x10\],0x0$', s) and 'logs_kept' not in f: f['logs_kept'] = {'%x' % x: 'nop'}
    F['%s:%x' % (prof, fn)] = f
    print(prof, kind, '%x' % fn, sorted(f), [list(v.items())[0] for v in f.values()])
json.dump(F, open(sys.argv[1], 'w'), indent=1)
