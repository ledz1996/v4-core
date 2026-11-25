"""Run an opdiff script against an alternative endpoint for one chain id.
Usage: python3 altrun.py <script.py> <chainId> <rpc url> <args...>"""
import sys, os, runpy
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff')
sys.path.insert(0, TOOLS)
import evm
script, cid, url = sys.argv[1], int(sys.argv[2]), sys.argv[3]
orig = evm.networks
def patched(*a, **k):
    out = []
    for n in orig(*a, **k):
        if n[0] == cid:
            out.append((cid, n[1] + '@' + url, url))
        else:
            out.append(n)
    return out
evm.networks = patched
sys.argv = [script] + sys.argv[4:]
runpy.run_path(os.path.join(TOOLS, script), run_name='__main__')
