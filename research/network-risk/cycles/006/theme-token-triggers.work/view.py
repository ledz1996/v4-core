# Compact view of digests: full body only for state-changing functions without an access modifier, and for balanceOf and
# the transfer hooks; one line for the rest.
import sys, re, glob, os
GUARD = re.compile(r'\b(only\w*|restricted|auth\w*|requiresAuth|whenAdmin|isOwner|ifAdmin|onlyRole\([^)]*\)|governance|hasRole)\b')
CORE = re.compile(r'^function (balanceOf|_update|_transfer|_beforeTokenTransfer|_afterTokenTransfer)\b')
SKIP = re.compile(r'^function (tryRecover|recover|recoverCalldata|tryRecoverCalldata|toEthSignedMessageHash|transfer|_spendAllowance|_burn|burn)\b')
def show(fn, maxbody=40):
    txt = open(fn).read()
    parts = re.split(r'\n(?=--- |## |#### )', txt)
    for p in parts:
        if p.startswith('####') or p.startswith('## '): print(p[:230]); continue
        lines = p.split('\n'); loc = lines[0]; body = lines[1:]
        if not body: continue
        head = ' '.join(x.strip() for x in body[:8]); head = head[:head.find('{')] if '{' in head else head
        if SKIP.match(head) and 'balanceOf' not in head: continue
        view = bool(re.search(r'\b(view|pure)\b', head)); internal = bool(re.search(r'\b(internal|private)\b', head))
        guarded = bool(GUARD.search(head))
        full = CORE.match(head) or (not view and not guarded)
        if full:
            print(loc); print('\n'.join(l[:210] for l in body[:maxbody]))
        else:
            print(loc, '|', head[:200], '| [view]' if view else '| [guarded]')
for a in sys.argv[1:]:
    for fn in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'digest', a + '_*.txt'))): show(fn)
