# Shared helpers for theme-hook-ledgers. Read-only JSON-RPC only. Reuses the cycle 5 helpers.
import sys, os, json, gzip
HERE = os.path.dirname(os.path.abspath(__file__))
C5 = os.path.join(HERE, '..', '..', '005', 'theme-shared-hooks.work')
C5U = os.path.join(HERE, '..', '..', '005', 'theme-unbacked-claims.work')
sys.path.insert(0, C5)
from lib import *
from config import CFG
from keccak import keccak256
HERE = os.path.dirname(os.path.abspath(__file__))  # lib.py defines its own HERE; restore ours
RAW = os.path.join(HERE, 'raw')
def urls(cid):
    n = net(cid); out = [n['rpc']] + [u for u in CFG[cid]['state'] if u != n['rpc']]
    return out
def mc3(u, calls, block='latest', frm=None, gas=None):
    """aggregate3 with allowFailure. calls: list of (target, calldata hex without 0x). returns list of (ok, bytes hex)"""
    def w(x): return int(x).to_bytes(32, 'big').hex()
    head = w(32) + w(len(calls)); offs = []; body = ''
    base = 32 * len(calls)
    for t, d in calls:
        offs.append(base + len(body) // 2)
        n = len(d) // 2
        body += adr(t) + w(1) + w(96) + w(n) + d.ljust((len(d) + 63) // 64 * 64, '0')
    data = '0x82ad56cb' + head + ''.join(w(o) for o in offs) + body
    tx = {'to': MC3, 'data': data}
    if frm: tx['from'] = frm
    if gas: tx['gas'] = hex(gas)
    r = rpc(u, 'eth_call', [tx, block], timeout=90)
    b = bytes.fromhex(r[2:])
    n = int.from_bytes(b[32:64], 'big'); out = []
    for i in range(n):
        o = 64 + int.from_bytes(b[64 + 32 * i:96 + 32 * i], 'big')
        ok = int.from_bytes(b[o:o + 32], 'big'); ln = int.from_bytes(b[o + 64:o + 96], 'big')
        out.append((bool(ok), b[o + 96:o + 96 + ln].hex()))
    return out
