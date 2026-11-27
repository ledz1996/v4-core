"""Cycle 28: the read functions whose native blocks no harness case had entered before this cycle (extsload(bytes32[]),
extsload(bytes32,uint256), exttload(bytes32[]), supportsInterface, owner, protocolFeeController, protocolFeesAccrued),
called by eth_call on each network's real PoolManager at one pinned block and compared with eth_getStorageAt at the same
block. Read-only. Each network is bracketed by web3_clientVersion. Usage: python3 -I rpc28.py <out.json> [chainIds]"""
import sys, os, json, time
NR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import rpc, keccak
NETS = json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']
B = json.load(open(os.path.join(NR, 'build', 'PoolManager.json')))['methodIdentifiers']
def w(x): return (x % (1 << 256)).to_bytes(32, 'big')
def sel(s): return bytes.fromhex(B[s])
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
SLOTS = [0, 1, 2, 3, 4, 5, 6, int.from_bytes(keccak(w(0) + w(1)), 'big')]
only = set(int(x) for x in sys.argv[2:])
out = {}
for n in NETS:
    cid = n['chainId']
    if only and cid not in only: continue
    url = n['rpc']; pm = n['poolManager']; r = {'rpc': url, 'pm': pm}
    try:
        r['clientBefore'] = rpc(url, 'web3_clientVersion', [])
        blk = rpc(url, 'eth_blockNumber', []); r['block'] = int(blk, 16)
        st = [rpc(url, 'eth_getStorageAt', [pm, hex(s), blk]) for s in SLOTS]
        st = [int(x, 16) for x in st]
        def call(data):
            try: return {'ok': True, 'ret': rpc(url, 'eth_call', [{'to': pm, 'data': '0x' + data.hex()}, blk])}
            except Exception as e: return {'ok': False, 'err': str(e)[:200]}  # noqa
        q = {'extsloadArray': call(sel('extsload(bytes32[])') + w(0x20) + w(len(SLOTS)) + b''.join(w(s) for s in SLOTS)),
             'extsloadRange0to7': call(sel('extsload(bytes32,uint256)') + w(0) + w(7)),
             'extsloadRangeWrap': call(sel('extsload(bytes32,uint256)') + w(0) + w((1 << 251) + 2)),
             'extsloadEmpty': call(sel('extsload(bytes32[])') + w(0x20) + w(0)),
             'exttloadArray': call(sel('exttload(bytes32[])') + w(0x20) + w(3) + w(CUR) + w(0) + w(1)),
             'si165': call(sel('supportsInterface(bytes4)') + bytes.fromhex('01ffc9a7') + bytes(28)),
             'si6909': call(sel('supportsInterface(bytes4)') + bytes.fromhex('0f632fb3') + bytes(28)),
             'siNone': call(sel('supportsInterface(bytes4)') + bytes.fromhex('ffffffff') + bytes(28)),
             'owner': call(sel('owner()')), 'controller': call(sel('protocolFeeController()')),
             'accruedNative': call(sel('protocolFeesAccrued(address)') + w(0))}
        r['calls'] = q; r['storage'] = [hex(x) for x in st]
        def words(k):
            x = q[k]
            if not x['ok']: return None
            b = bytes.fromhex(x['ret'][2:]); return [int.from_bytes(b[i:i + 32], 'big') for i in range(0, len(b), 32)]
        chk = {}
        a = words('extsloadArray'); chk['extsloadArray'] = a == [0x20, len(SLOTS)] + st
        a = words('extsloadRange0to7'); chk['extsloadRange'] = a == [0x20, 7] + st[:7]
        a = words('extsloadRangeWrap'); chk['extsloadRangeWrap'] = a == [0x20, (1 << 251) + 2, st[0], st[1]]
        a = words('extsloadEmpty'); chk['extsloadEmpty'] = a is not None and a[:2] == [0x20, 0] and len(a) == 2
        a = words('exttloadArray'); chk['exttloadArray'] = a == [0x20, 3, 0, 0, 0]
        chk['supportsInterface'] = (words('si165'), words('si6909'), words('siNone')) == ([1], [1], [0])
        chk['owner'] = words('owner') == [st[0] & ((1 << 160) - 1)]
        chk['controller'] = words('controller') == [st[2] & ((1 << 160) - 1)]
        chk['accruedNative'] = words('accruedNative') == [st[7]]
        r['checks'] = chk; r['allOk'] = all(chk.values())
        r['clientAfter'] = rpc(url, 'web3_clientVersion', [])
    except Exception as e:  # noqa
        r['error'] = str(e)[:300]
    out[str(cid)] = r
    print(cid, n['name'], r.get('clientBefore', '')[:60], r.get('block'), r.get('allOk'), {k: v for k, v in r.get('checks', {}).items() if not v}, r.get('error', ''), flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
