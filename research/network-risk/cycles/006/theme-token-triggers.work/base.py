# Shared helpers for theme-token-triggers. Read-only JSON-RPC only. Builds on the cycle 5 helpers.
import os, sys, json, gzip, time
HERE = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.join(HERE, '..', '..', '005', 'theme-assigned-balance.work')
sys.path.insert(0, W5)
from common import *            # post, rpc, batch, sel, u256, adr, NETS, net, universe, urls2, ecall, RAW (cycle 5 raw)
from asm import assemble, MULTI, FWD, FWDN, OPS
from abi import split_types, encode, supported
RAW5 = RAW
HERE6 = os.path.dirname(os.path.abspath(__file__))   # common overwrites HERE with the cycle 5 directory
RAW6 = os.path.join(HERE6, 'raw')
A = '0x00000000000000000000000000000000000a11ce'; SINK = '0x00000000000000000000000000000000005111c0'
TS_STUB = assemble('TIMESTAMP 0 MSTORE NUMBER 0x20 MSTORE 0x40 0 RETURN')
def jz(fn): return json.load(gzip.open(fn, 'rt'))
def ecall_t(cid, url, to, data, override=None, frm=None, gas=None, block='latest', dt=0, now=None, timeout=90):
    """eth_call with state override and, when dt > 0, a block override that moves the block time forward."""
    tx = {'to': to, 'data': data}
    if frm: tx['from'] = frm
    if gas: tx['gas'] = hex(gas)
    p = [tx, block, override or {}]
    if dt: p.append({'time': hex(now + dt)})
    j = post(url, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': p}, timeout=timeout, tries=1)
    if 'error' in j: return {'error': j['error']}
    return j['result']
