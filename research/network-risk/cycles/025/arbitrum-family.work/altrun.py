"""Run an opdiff script against alternative Arbitrum One endpoints (lead L-1038).
Usage: python3 altrun.py <script.py> <args...>   (chain ids in args select from ALT)
The pseudo chain ids 4216101 and 4216102 stand for the publicnode and pocket endpoints of Arbitrum One."""
import sys, runpy, os
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
orig = evm.networks
ALT = [(4216101, 'Arb1 publicnode', 'https://arbitrum-one-rpc.publicnode.com'),
       (4216102, 'Arb1 pocket', 'https://arb-one.api.pocket.network')]
def networks(*a, **k):
    return [n for n in orig(*a, **k) if n[0] == 1] + ALT
evm.networks = networks
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
runpy.run_path(os.path.join(T, script), run_name='__main__')
