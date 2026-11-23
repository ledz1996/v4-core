# Basic facts about a token: name, symbol, decimals, totalSupply, code size, EIP-1967 implementation, balance of the PoolManager.
import sys
from lib import *
from config import CFG
def s(h):
    try:
        b = bytes.fromhex(h[2:])
        if len(b) >= 64: n = int.from_bytes(b[32:64], 'big'); return b[64:64 + n].decode('utf8', 'replace')
        return b.rstrip(b'\0').decode('utf8', 'replace')
    except Exception: return h[:40]
def info(cid, t, block='latest', url=None):
    n = net(cid); u = url or CFG[cid]['state'][0]; pm = n['poolManager']; o = {'token': t}
    def c(data):
        try: return rpc(u, 'eth_call', [{'to': t, 'data': data}, block])
        except Exception as e: return 'ERR ' + str(e)[:80]
    o['name'] = s(c('0x06fdde03')); o['symbol'] = s(c('0x95d89b41'))
    d = c('0x313ce567'); o['decimals'] = int(d, 16) if d.startswith('0x') and len(d) > 2 else d
    ts = c('0x18160ddd'); o['totalSupply'] = int(ts, 16) if ts.startswith('0x') and len(ts) > 2 else ts
    b = c('0x70a08231' + pm[2:].lower().rjust(64, '0')); o['pmBalance'] = int(b, 16) if b.startswith('0x') and len(b) > 2 else b
    code = rpc(u, 'eth_getCode', [t, block]); o['codeLen'] = (len(code) - 2) // 2; o['codeHead'] = code[:60]
    impl = rpc(u, 'eth_getStorageAt', [t, '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc', block]); o['impl1967'] = '0x' + impl[-40:]
    return o
if __name__ == '__main__':
    print(json.dumps(info(int(sys.argv[1]), sys.argv[2]), indent=1))
