"""Runs one tools/opdiff script with evm.networks() reading another networks file (here: Arc through PublicNode).
usage: python3 withnet.py <networks.json> <script.py> [args...]"""
import sys, os, runpy
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
NET = os.path.abspath(sys.argv[1]); orig = evm.networks
evm.networks = lambda path=NET: orig(NET)
script = os.path.join(T, sys.argv[2]); sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name='__main__')
