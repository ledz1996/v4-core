"""Run an opdiff script against several Ethereum mainnet endpoints (other clients and versions).
Usage: python3 altrun.py <script.py> <args...>   (pseudo chain ids 1001.. name the endpoints)"""
import sys, os, runpy
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm
ALT = [(1, 'Ethereum reth v2.11.0 (publicnode)', 'https://ethereum-rpc.publicnode.com'),
       (1011, 'Ethereum geth v1.17.9 (blockpi)', 'https://ethereum.public.blockpi.network/v1/rpc/public'),
       (1012, 'Ethereum geth v1.17.5 (blockrazor)', 'https://eth.blockrazor.xyz'),
       (1014, 'Ethereum geth v1.16.8 (nodereal)', 'https://eth-mainnet.nodereal.io/v1/1659dfb40aa24bbb8153a677b98064d7'),
       (1004, 'Ethereum reth v2.7.0 (nodies)', 'https://eth-pokt.nodies.app'),
       (1015, 'Ethereum geth v1.17.9 go1.25.14 (pocket)', 'https://eth.api.pocket.network')]
evm.networks = lambda *a, **k: ALT
script = sys.argv[1]; sys.argv = [script] + sys.argv[2:]
runpy.run_path(os.path.join(OPD, script), run_name='__main__')
