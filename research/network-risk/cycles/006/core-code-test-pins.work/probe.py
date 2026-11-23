"""Read-only behaviour probe of the deployed PoolManagers for the guards that no test in test/ pins.
Uses eth_call only. A forwarder stub is placed at an unused address by state override.
No transaction is sent."""
import json, subprocess, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keccak import keccak256

def k(b):
    r = keccak256(b if isinstance(b, (bytes, bytearray)) else b.encode())
    return r if isinstance(r, (bytes, bytearray)) else bytes.fromhex(r)
def sel(s): return k(s)[:4]
def w(x):
    if isinstance(x, str): x = int(x, 16)
    return (x % (1 << 256)).to_bytes(32, 'big')

OP = dict(STOP=0x00, ADD=0x01, SUB=0x03, LT=0x10, GT=0x11, EQ=0x14, ISZERO=0x15, SHR=0x1c, CALLER=0x33,
          CALLDATALOAD=0x35, CALLDATASIZE=0x36, CALLDATACOPY=0x37, RETURNDATASIZE=0x3d, RETURNDATACOPY=0x3e,
          POP=0x50, MLOAD=0x51, MSTORE=0x52, JUMP=0x56, JUMPI=0x57, GAS=0x5a, JUMPDEST=0x5b,
          DUP1=0x80, DUP3=0x82, CALL=0xf1, RETURN=0xf3)

def assemble(prog):
    # two passes; labels use PUSH2
    out = bytearray(); labels = {}; fix = []
    for ins in prog:
        if isinstance(ins, tuple) and ins[0] == 'label':
            labels[ins[1]] = len(out); out.append(OP['JUMPDEST'])
        elif isinstance(ins, tuple) and ins[0] == 'push':
            v = ins[1]
            if isinstance(v, str):  # label
                out.append(0x61); fix.append((len(out), v)); out += b'\x00\x00'
            else:
                n = ins[2] if len(ins) > 2 else max(1, (v.bit_length() + 7) // 8)
                out.append(0x5f + n); out += v.to_bytes(n, 'big')
        else:
            out.append(OP[ins])
    for pos, name in fix:
        out[pos:pos + 2] = labels[name].to_bytes(2, 'big')
    return bytes(out)

def stub_code(manager):
    M = int(manager, 16)
    P = lambda v, n=None: ('push', v, n) if n else ('push', v)
    prog = [
        P(M, 20), 'CALLER', 'EQ', P('cb'), 'JUMPI',
        # entry: forward calldata to the manager, return success word followed by the return data
        'CALLDATASIZE', P(0), P(0), 'CALLDATACOPY',
        P(0), P(0), 'CALLDATASIZE', P(0), P(0), P(M, 20), 'GAS', 'CALL',
        P(0), 'MSTORE',
        'RETURNDATASIZE', P(0), P(0x20), 'RETURNDATACOPY',
        'RETURNDATASIZE', P(0x20), 'ADD', P(0), 'RETURN',
        ('label', 'cb'),
        P(0x44), P(0x300, 2), 'MSTORE',
        P(0x24), 'CALLDATALOAD', P(0x44), 'ADD', P(0x320, 2), 'MSTORE',
        P(0x440, 2), P(0x340, 2), 'MSTORE',
        ('label', 'loop'),
        P(0x320, 2), 'MLOAD', P(0x300, 2), 'MLOAD', 'LT', 'ISZERO', P('done'), 'JUMPI',
        P(0x300, 2), 'MLOAD', 'CALLDATALOAD', P(0xf0), 'SHR',
        P(0x300, 2), 'MLOAD', P(2), 'ADD', P(0x300, 2), 'MSTORE',
        'DUP1', P(0x300, 2), 'MLOAD', P(0), 'CALLDATACOPY',
        'DUP1', P(0x300, 2), 'MLOAD', 'ADD', P(0x300, 2), 'MSTORE',
        P(0), P(0x200, 2), 'MSTORE',
        P(0x20), P(0x200, 2), 'DUP3', P(0), P(0), P(M, 20), 'GAS', 'CALL',
        P(0x340, 2), 'MLOAD', 'MSTORE',
        'POP',
        P(0x200, 2), 'MLOAD', P(0x340, 2), 'MLOAD', P(0x20), 'ADD', 'MSTORE',
        P(0x340, 2), 'MLOAD', P(0x40), 'ADD', P(0x340, 2), 'MSTORE',
        P('loop'), 'JUMP',
        ('label', 'done'),
        P(0x20), P(0x400, 2), 'MSTORE',
        P(0x440, 2), P(0x340, 2), 'MLOAD', 'SUB', P(0x420, 2), 'MSTORE',
        P(0x400, 2), P(0x340, 2), 'MLOAD', 'SUB', P(0x400, 2), 'RETURN',
    ]
    return assemble(prog)

STUB = '0x' + k('core-code-test-pins stub')[-20:].hex()
VICT = '0x' + k('core-code-test-pins third party')[-20:].hex()
CUR = '0x' + k('core-code-test-pins codeless currency')[-20:].hex()
FROM = '0x' + k('core-code-test-pins sender')[-20:].hex()
BIG = 1 << 127

def cd(sig, *args):
    return sel(sig) + b''.join(w(a) for a in args)
def unlock_call(inner):
    data = b''.join(len(c).to_bytes(2, 'big') + c for c in inner)
    pad = (-len(data)) % 32
    return sel('unlock(bytes)') + w(0x20) + w(len(data)) + data + b'\x00' * pad

mint = lambda to, amt: cd('mint(address,uint256,uint256)', to, CUR, amt)
burn = lambda frm, amt: cd('burn(address,uint256,uint256)', frm, CUR, amt)
SEQ = {
  'P_selfMintBurn': [mint(STUB, 5), burn(STUB, 5)],
  'N1_mintOnly': [mint(VICT, 5)],
  'N2_mintThirdThenBurnThird': [mint(VICT, 5), burn(VICT, 5)],
  'C_twoMintsOneBurn': [mint(STUB, 5), mint(STUB, 3), burn(STUB, 8)],
  'G_guards': [
      cd('settleFor(address)', VICT),
      cd('clear(address,uint256)', CUR, 1),
      mint(STUB, BIG),
      cd('take(address,address,uint256)', CUR, STUB, BIG),
      burn(STUB, BIG),
      cd('take(address,address,uint256)', CUR, STUB, 0),
      cd('sync(address)', CUR),
      cd('sync(address)', 0),
      cd('settle()'),
      cd('unlock(bytes)', 0x20, 0),
  ],
}
LOCKED = {
  'settleFor': cd('settleFor(address)', VICT),
  'clear': cd('clear(address,uint256)', CUR, 0),
  'settle': cd('settle()'),
  'take': cd('take(address,address,uint256)', CUR, STUB, 0),
  'mint': mint(STUB, 0),
  'burn': burn(STUB, 0),
  'sync0': cd('sync(address)', 0),
}

def rpc(url, method, params, timeout=40):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
    for attempt in range(3):
        try:
            r = subprocess.run(['curl', '-sS', '--max-time', str(timeout), '-H', 'content-type: application/json',
                                '-d', body, url], capture_output=True, text=True, timeout=timeout + 10)
            if r.stdout.strip():
                return json.loads(r.stdout)
            err = r.stderr.strip()[:200]
        except Exception as e:
            err = repr(e)[:200]
        time.sleep(1.5)
    return {'error': {'message': 'transport: ' + err}}

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    nets = json.load(open(os.path.join(here, '..', '..', '..', 'state', 'networks.json')))
    if isinstance(nets, dict): nets = nets.get('networks', nets)
    only = set(int(x) for x in sys.argv[1:])
    res = {}
    for n in nets:
        cid = n['chainId']
        if only and cid not in only: continue
        url, pm = n['rpc'], n['poolManager']
        out = {'name': n['name'], 'poolManager': pm, 'rpc': url}
        bn = rpc(url, 'eth_blockNumber', [])
        out['block'] = bn.get('result')
        blk = out['block'] or 'latest'
        out['codeAt'] = {a: (rpc(url, 'eth_getCode', [a, blk]).get('result')) for a in (STUB, VICT, CUR, FROM)}
        pmcode = rpc(url, 'eth_getCode', [pm, blk]).get('result') or '0x'
        out['pmCodeLen'] = (len(pmcode) - 2) // 2
        code = '0x' + stub_code(pm).hex()
        out['locked'] = {}
        for name, c in LOCKED.items():
            r = rpc(url, 'eth_call', [{'from': FROM, 'to': pm, 'data': '0x' + c.hex()}, blk])
            out['locked'][name] = r.get('result') if 'result' in r else {'error': r.get('error')}
        out['seq'] = {}
        for name, inner in SEQ.items():
            r = rpc(url, 'eth_call', [{'from': FROM, 'to': STUB, 'data': '0x' + unlock_call(inner).hex()}, blk,
                                      {STUB: {'code': code}}])
            out['seq'][name] = r.get('result') if 'result' in r else {'error': r.get('error')}
        res[str(cid)] = out
        print(cid, n['name'], 'block', out['block'], 'pmCodeLen', out['pmCodeLen'], flush=True)
    path = os.path.join(here, 'raw', 'probe_results.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(res)
    json.dump(old, open(path, 'w'), indent=1)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'show':
        print('stub', STUB, 'third', VICT, 'cur', CUR, 'from', FROM)
        print(stub_code('0x000000000004444c5dc75cB358380D2e3dE08A90').hex())
    else:
        main()
