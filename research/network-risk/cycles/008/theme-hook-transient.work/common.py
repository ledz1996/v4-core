# Shared helpers for theme-hook-transient (cycle 8). Read-only JSON-RPC only. Reuses cycle 5 and 6 helpers and data.
import sys, os, json, gzip
HERE = os.path.dirname(os.path.abspath(__file__))
C5 = os.path.join(HERE, '..', '..', '005', 'theme-shared-hooks.work')
C6 = os.path.join(HERE, '..', '..', '006', 'theme-hook-ledgers.work')
sys.path.insert(0, C5)
from lib import *
from config import CFG
from keccak import keccak256
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
def urls(cid):
    n = net(cid); return [n['rpc']] + [u for u in CFG[cid]['state'] if u != n['rpc']]
def k4(sig): return keccak256(sig.encode()).hex()[:8]
