"""Cycle 39 Task 5 (live part): on each network's endpoint from state/networks.json, one eth_simulateV1 block of
seven calls (each call is its own transaction in the simulated block), bracketed by web3_clientVersion:
  c0 control: helper H0 (state override) calls PoolManager.sync(MOCK) and reads CURRENCY_SLOT and RESERVES_OF_SLOT
     back through exttload(bytes32) in the same transaction (must be MOCK and 0x1234: proves the words get set);
  c1 the EOA calls PoolManager.sync(MOCK) directly and the transaction succeeds, leaving both words set at its end;
  c2 the EOA reads LOCK, NONZERO_DELTA_COUNT, CURRENCY, RESERVES_OF and three delta words with exttload(bytes32[]);
  c3 helper H1 calls sync(MOCK), writes nothing else and reverts at the end (late revert);
  c4 the same read as c2;
  c5 a deposit-like call: from the OP Stack L1 attributes depositor 0xdead...0001 to sync(MOCK) (an ordinary call in
     the simulator; no endpoint takes a type 0x7e transaction here);
  c6 the same read as c2.
MOCK (state override) answers every call with the word 0x1234, so balanceOf(PoolManager) = 0x1234.
Expected: c0 returns (MOCK, 0x1234); c2, c4, c6 return seven zero words. Read-only: nothing is sent.
usage: python3 -I live_sim.py <out.json> [chainId | chainId@url ...]  (chainId@url: another public endpoint)"""
import json, sys, time, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak

NETS = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
NETS = NETS if isinstance(NETS, list) else NETS.get('networks', NETS)
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
RES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95   # CurrencyReserves.RESERVES_OF_SLOT
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9   # CurrencyReserves.CURRENCY_SLOT
MOCK = 0x00000000000000000000000000000000c0de7001
H0 = 0x00000000000000000000000000000000c0de7002
H1 = 0x00000000000000000000000000000000c0de7003
EOA = 0x00000000000000000000000000000000c0de70ee
DEP = 0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001


def p(n, v): return bytes([0x5f + n]) + v.to_bytes(n, 'big')


def delta_slot(target, currency):
    # CurrencyDelta: keccak256(abi.encode(target, currency)) (src/libraries/CurrencyDelta.sol)
    return int.from_bytes(keccak(target.to_bytes(32, 'big') + currency.to_bytes(32, 'big')), 'big')


def sync_call(pm):
    c = p(4, 0xa5841194) + p(1, 0xe0) + b'\x1b' + p(1, 0) + b'\x52'      # mstore(0, sel << 224)
    c += p(20, MOCK) + p(1, 4) + b'\x52'                                  # mstore(4, MOCK)
    c += p(1, 0) + p(1, 0) + p(1, 36) + p(1, 0) + p(1, 0) + p(20, pm) + b'\x5a\xf1\x50'   # call(gas, pm, 0, 0, 36, 0, 0); pop
    return c


def read_into(pm, slot, dst):
    c = p(4, 0xf135baaa) + p(1, 0xe0) + b'\x1b' + p(1, 0) + b'\x52' + p(32, slot) + p(1, 4) + b'\x52'
    c += p(1, 32) + p(1, dst) + p(1, 36) + p(1, 0) + p(20, pm) + b'\x5a\xfa\x50'          # staticcall(gas, pm, 0, 36, dst, 32)
    return c


def h0(pm): return sync_call(pm) + read_into(pm, CUR, 0x40) + read_into(pm, RES, 0x60) + p(1, 0x40) + p(1, 0x40) + b'\xf3'
def h1(pm): return sync_call(pm) + p(1, 0) + p(1, 0) + b'\xfd'
MOCKCODE = p(2, 0x1234) + p(1, 0) + b'\x52' + p(1, 32) + p(1, 0) + b'\xf3'


def rpc(url, method, params, timeout=40):
    body = json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'rpc-client/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return dict(http_error=e.code, body=e.read()[:300].decode('latin1'))
    except Exception as e:
        return dict(exception=repr(e)[:300])


def h(x, n=20): return '0x' + x.to_bytes(n, 'big').hex()


def main():
    out = sys.argv[1]; only = {int(x.split('@')[0]) for x in sys.argv[2:]}
    alt = {int(x.split('@')[0]): x.split('@', 1)[1] for x in sys.argv[2:] if '@' in x}
    res = []
    for n in NETS:
        cid = n['chainId']
        if only and cid not in only: continue
        url = alt.get(cid) or n.get('rpc') or n.get('rpcUrl'); pm = int(n['poolManager'], 16)
        slots = [LOCK, NZDC, CUR, RES, delta_slot(EOA, MOCK), delta_slot(H1, MOCK), delta_slot(DEP, MOCK)]
        rd = '0x9bf6645f' + (32).to_bytes(32, 'big').hex() + len(slots).to_bytes(32, 'big').hex() + ''.join(s.to_bytes(32, 'big').hex() for s in slots)
        sy = '0xa5841194' + MOCK.to_bytes(32, 'big').hex()
        calls = [dict(**{'from': h(EOA), 'to': h(H0), 'data': '0x'}),
                 dict(**{'from': h(EOA), 'to': h(pm), 'data': sy}),
                 dict(**{'from': h(EOA), 'to': h(pm), 'data': rd}),
                 dict(**{'from': h(EOA), 'to': h(H1), 'data': '0x'}),
                 dict(**{'from': h(EOA), 'to': h(pm), 'data': rd}),
                 dict(**{'from': h(DEP), 'to': h(pm), 'data': sy}),
                 dict(**{'from': h(EOA), 'to': h(pm), 'data': rd})]
        for c in calls: c['gas'] = hex(3_000_000)
        ov = {h(MOCK): {'code': '0x' + MOCKCODE.hex()}, h(H0): {'code': '0x' + h0(pm).hex()}, h(H1): {'code': '0x' + h1(pm).hex()}}
        r = dict(chainId=cid, name=n.get('name'), url=url, started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        r['client_before'] = rpc(url, 'web3_clientVersion', []).get('result')
        sim = rpc(url, 'eth_simulateV1', [dict(blockStateCalls=[dict(stateOverrides=ov, calls=calls)], validation=False), 'latest'], timeout=60)
        r['client_after'] = rpc(url, 'web3_clientVersion', []).get('result')
        r['raw'] = sim
        if 'result' in sim and isinstance(sim['result'], list) and sim['result']:
            cs = sim['result'][0].get('calls', [])
            r['calls'] = [dict(status=c.get('status'), ret=c.get('returnData'), err=c.get('error')) for c in cs]
            r['block'] = sim['result'][0].get('number')
            ctrl = cs[0].get('returnData', '') if cs else ''
            exp_ctrl = '0x' + MOCK.to_bytes(32, 'big').hex() + (0x1234).to_bytes(32, 'big').hex()
            r['control_ok'] = ctrl == exp_ctrl
            zero = '0x' + (32).to_bytes(32, 'big').hex() + len(slots).to_bytes(32, 'big').hex() + '00' * 32 * len(slots)
            r['reads_zero'] = [cs[i].get('returnData') == zero for i in (2, 4, 6)] if len(cs) >= 7 else None
            r['sync_status'] = [cs[i].get('status') for i in (1, 3, 5)] if len(cs) >= 7 else None
            del r['raw']
        r['verdict'] = ('pass' if r.get('control_ok') and r.get('reads_zero') == [True, True, True]
                        else ('fail' if r.get('control_ok') else 'not served' if 'calls' not in r else 'control failed'))
        print(cid, n.get('name'), r['client_before'], r['verdict'], r.get('sync_status'), r.get('reads_zero'),
              '' if 'calls' in r else json.dumps(sim)[:200])
        res.append(r)
    json.dump(res, open(out, 'w'), indent=1)


main()
