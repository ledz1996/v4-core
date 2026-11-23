# Triage view: for each digest, the bodies of balanceOf and the transfer hooks when they are not the plain library version,
# and of every unguarded state-changing external function that takes an address parameter. Other functions as one line.
import sys, re, glob, os
GUARD = re.compile(r'\b(only\w*|restricted|auth\w*|requiresAuth|whenAdmin|isOwner|ifAdmin|governance|hasRole|isAdmin\w*|admin\w*|checkRole\w*|allow\(|canCall|requiresRole|isController|onlyRole)\b')
CORE = re.compile(r'^function (balanceOf|_update|_transfer|_beforeTokenTransfer|_afterTokenTransfer)\b')
PLAIN = re.compile(r'return\s+(\$\.)?_?balances?\[[^\]]+\];|return\s+super\.balanceOf|^\s*super\._update\(from, to, value\);\s*$|return _getERC20Storage\(\)\._balances')
SKIP = re.compile(r'^function (tryRecover|recover|recoverCalldata|tryRecoverCalldata|toEthSignedMessageHash|transfer|_spendAllowance|_burn|burn|burnFrom)\b')
def show(fn, maxbody=60, brief=True):
    txt = open(fn).read()
    parts = re.split(r'\n(?=--- |## |#### )', txt)
    seen = set()
    for p in parts:
        if p.startswith('####'): print('\n' + p[:200]); continue
        if p.startswith('## '): print(p[:150]); continue
        lines = p.split('\n'); loc = lines[0]; body = lines[1:]
        if not body: continue
        btxt = '\n'.join(body)
        if btxt in seen or btxt.lstrip().startswith('//'): continue
        if all(l.strip().startswith('//') for l in body[1:] if l.strip()) and len(body) > 2: continue
        seen.add(btxt)
        head = ' '.join(x.strip() for x in body[:10]); head = head[:head.find('{')] if '{' in head else head
        if SKIP.match(head): continue
        view = bool(re.search(r'\b(view|pure|constant)\b', head)); internal = bool(re.search(r'\b(internal|private)\b', head))
        guarded = bool(GUARD.search(head)) or bool(re.search(r'require\(\s*(msg\.sender|_msgSender\(\))\s*==|if\s*\(\s*(msg\.sender|_msgSender\(\))\s*!=|onlyOwner|_checkOwner|_checkRole|_onlyRole', '\n'.join(body[:8])))
        hasaddr = bool(re.search(r'\(\s*[^)]*\baddress\b', head))
        if CORE.match(head):
            core = '\n'.join(body)
            if len(body) <= 6 and PLAIN.search(core) and 'balanceOf' in head: print(loc, '| plain balanceOf'); continue
            print(loc); print('\n'.join(l[:200] for l in body[:maxbody])); continue
        if not view and not guarded and not internal and hasaddr:
            print(loc, '<< UNGUARDED WITH ADDRESS'); print('\n'.join(l[:200] for l in body[:maxbody]))
        elif not brief or (not view and not guarded):
            print(loc, '|', head[:170], '| [view]' if view else ('| [guarded]' if guarded else ('| [internal]' if internal else '| [no address]')))
for a in sys.argv[1:]:
    for fn in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', 'digest', a + '_*.txt'))): show(fn)
