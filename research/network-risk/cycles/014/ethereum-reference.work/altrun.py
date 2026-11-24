"""Run an opdiff script against other Ethereum mainnet endpoints (other clients and versions).
Usage: python3 altrun.py <script.py> <args...>   (pseudo chain ids 1001.. name the endpoints)"""
import sys, os, runpy
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
ALT = [(1001, 'Ethereum geth v1.16.7 (1rpc)', 'https://1rpc.io/eth'),
       (1002, 'Ethereum geth v1.16.7 (bloxroute)', 'https://eth.rpc.blxrbdn.com'),
       (1003, 'Ethereum reth v2.10.0 evm2 (blastapi)', 'https://eth-mainnet.public.blastapi.io'),
       (1004, 'Ethereum reth v2.7.0 revm (nodies)', 'https://eth-pokt.nodies.app'),
       (1005, 'Ethereum reth v2.6.0 revm (flashbots)', 'https://rpc.flashbots.net'),
       (1006, 'Ethereum drpc', 'https://eth.drpc.org')]
evm.networks = lambda *a, **k: ALT
script = sys.argv[1]; sys.argv = [script] + sys.argv[2:]
runpy.run_path(os.path.join(OPD, script), run_name='__main__')
