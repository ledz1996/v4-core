"""L-487 added shape on Ethereum. Read-only: one eth_call per target with a state override that puts a stub at the
PoolManager address (balance 1 ETH). The stub staticcalls X.balanceOf(PoolManager), then clears storage slot 0 of the
PoolManager address, sends 1 wei to an unrelated codeless address (shape A) or to X itself with empty calldata (shape B),
writes transient slot 0, and staticcalls X.balanceOf(PoolManager) again. It returns both success flags, both return
sizes and the first word of both answers. Usage: python3 l487.py <out.json>"""
import sys, json, os, time, importlib.util
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
spec = importlib.util.spec_from_file_location('targets', '/home/user/v4-core/research/network-risk/cycles/008/ethereum-reference.work/targets.py')
tg = importlib.util.module_from_spec(spec); spec.loader.exec_module(tg)
URL = 'https://ethereum-rpc.publicnode.com'
PM = '0x000000000004444c5dc75cB358380D2e3dE08A90'
OTHER = 0x00000000000000000000000000000000c0ffee24

def push(v):
    b = v.to_bytes(max(1, (v.bit_length() + 7) // 8), 'big')
    return bytes([0x5f + len(b)]) + b if v else b'\x5f'

def stub(shape):
    c = b''
    # target address = calldataload(0) kept at memory 0x300
    c += push(0) + b'\x35' + push(0x300) + b'\x52'
    def read(outoff, flagoff):
        r = push(0x70a08231 << 224) + push(0) + b'\x52'          # mstore(0, selector)
        r += b'\x30' + push(4) + b'\x52'                          # mstore(4, address())
        r += push(32) + push(outoff) + push(36) + push(0)          # retSize retOff argSize argOff
        r += push(0x300) + b'\x51' + b'\x5a' + b'\xfa'             # target, gas, STATICCALL
        r += push(flagoff) + b'\x52'                               # mstore(flag, ok)
        r += b'\x3d' + push(flagoff + 0x40) + b'\x52'              # mstore(flag+0x40, returndatasize)
        return r
    c += read(0x100, 0x200)
    c += push(0) + push(0) + b'\x55'                              # sstore(0, 0)
    to = push(OTHER) if shape == 'A' else push(0x300) + b'\x51'
    c += push(0) + push(0) + push(0) + push(0) + push(1) + to + b'\x5a' + b'\xf1'  # call(gas, to, 1, 0,0,0,0)
    c += push(0x280) + b'\x52'                                    # mstore(0x280, ok of value call)
    c += push(1) + push(0) + b'\x5d'                              # tstore(0, 1)
    c += read(0x120, 0x220)
    # return 0x100..0x2a0
    c += push(0x1a0) + push(0x100) + b'\xf3'
    return c

def run():
    out = []
    for cat, label, addr in tg.T:
        row = {'cat': cat, 'label': label, 'addr': addr}
        for shape in 'AB':
            code = stub(shape)
            data = int(addr, 16).to_bytes(32, 'big')
            tx = {'to': PM, 'data': '0x' + data.hex(), 'gas': hex(30_000_000), 'from': '0x' + 'ab' * 20}
            try:
                r = None
                for k in range(8):
                    try:
                        r = bytes.fromhex(evm.rpc(URL, 'eth_call', [tx, 'latest', {PM: {'code': '0x' + code.hex(), 'balance': hex(10**18)}}])[2:]); break
                    except Exception as e:
                        if k == 7: raise
                        time.sleep(2 + 2 * k)
                time.sleep(0.4)
                w = [int.from_bytes(r[i:i + 32], 'big') for i in range(0, len(r), 32)]
                # words: 0x100 r1, 0x120 r2, ..., 0x200 ok1, 0x220 ok2, 0x240 size1, 0x260 size2, 0x280 valueok
                g = lambda off: w[(off - 0x100) // 32]
                row[shape] = {'ok1': g(0x200), 'ok2': g(0x220), 'size1': g(0x240), 'size2': g(0x260), 'r1': hex(g(0x100)), 'r2': hex(g(0x120)), 'valueCallOk': g(0x280)}
            except Exception as e:
                row[shape] = {'error': str(e)[:200]}
        a = row.get('A', {})
        row['differA'] = a.get('r1') != a.get('r2') or a.get('ok1') != a.get('ok2')
        b = row.get('B', {})
        row['differB'] = b.get('r1') != b.get('r2') or b.get('ok1') != b.get('ok2')
        out.append(row)
        print(label, 'A', a, 'B', b, flush=True)
    return out

if __name__ == '__main__':
    res = run()
    ver = evm.rpc(URL, 'web3_clientVersion', [])
    blk = evm.rpc(URL, 'eth_blockNumber', [])
    json.dump({'endpoint': URL, 'clientVersion': ver, 'block': int(blk, 16), 'targets': len(res),
               'differA': [r['label'] for r in res if r['differA']], 'differB': [r['label'] for r in res if r['differB']], 'rows': res}, open(sys.argv[1], 'w'), indent=1)
    print('differA', [r['label'] for r in res if r['differA']]); print('differB', [r['label'] for r in res if r['differB']])
