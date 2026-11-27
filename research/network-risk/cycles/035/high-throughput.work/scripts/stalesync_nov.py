"""Task 4: does a bare sync(token) at the end of one transaction leave the synced currency and reserves for the next?
eth_simulateV1, one simulated block, on the deployed PoolManager. Nothing is sent.
 tx1: EOA -> PoolManager.sync(T)        T = a state-overridden token whose balanceOf returns 0x1234 for every caller
 tx2: EOA -> PoolManager.exttload([CURRENCY_SLOT, RESERVES_OF_SLOT])  (src/libraries/CurrencyReserves.sol:11-13)
 tx3: EOA -> driver D (pmdiff.py driver, pointed at the deployed PoolManager): unlock, then in the callback
      exttload(CURRENCY_SLOT), exttload(RESERVES_OF_SLOT), settle() with value 0, exttload(CURRENCY_SLOT); reverts with the record
 control tx4: D runs sync(T) then exttload of both slots inside one unlock (same transaction): must show T and 0x1234.
Usage: python3 stalesync.py <label> <url> <pm>"""
import sys, os, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pmdiff as P
from evm import keccak, rpc
label, url, pm = sys.argv[1], sys.argv[2], sys.argv[3]
P.PM = pm
D = '0x00000000000000000000000000000000d21fe001'; T = '0x000000000000000000000000000000000070c0e1'; EOA = '0x00000000000000000000000000000000000e0a01'
TOKEN = bytes.fromhex('6112345f5260205ff3')  # PUSH2 0x1234 PUSH0 MSTORE PUSH1 32 PUSH0 RETURN
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9; RES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
def item(cd): return len(cd).to_bytes(2, 'big') + cd
SYNC = keccak(b'sync(address)')[:4] + P.w(int(T, 16))
EXTA = keccak(b'exttload(bytes32[])')[:4] + P.w(0x20) + P.w(2) + P.w(CUR) + P.w(RES)
SETTLE = keccak(b'settle()')[:4]
drv = P.driver()
s3 = b''.join(item(c) for c in [P.S_EXTTLOAD + P.w(CUR), P.S_EXTTLOAD + P.w(RES), SETTLE, P.S_EXTTLOAD + P.w(CUR)]) + b'\0\0'
s4 = b''.join(item(c) for c in [SYNC, P.S_EXTTLOAD + P.w(CUR), P.S_EXTTLOAD + P.w(RES)]) + b'\0\0'
calls = [{'from': EOA, 'to': pm, 'data': '0x' + SYNC.hex(), 'gas': hex(300000)},
         {'from': EOA, 'to': pm, 'data': '0x' + EXTA.hex(), 'gas': hex(300000)},
         {'from': EOA, 'to': D, 'data': '0x' + s3.hex(), 'gas': hex(600000)},
         {'from': EOA, 'to': D, 'data': '0x' + s4.hex(), 'gas': hex(600000)}]
ov = {D: {'code': '0x' + drv.hex()}, T: {'code': '0x' + TOKEN.hex()}, EOA: {'balance': hex(10 ** 18)}}
out = {'label': label, 'url': url, 'pm': pm}
try: out['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [])
except Exception as e: out['clientVersionBefore'] = 'ERR ' + str(e)[:200]
try:
    r = rpc(url, 'eth_simulateV1', [{'blockStateCalls': [{'stateOverrides': ov, 'calls': calls}]}, 'latest'], timeout=120)
    res = r[0]['calls']; out['raw'] = res
    def words(h): b = bytes.fromhex(h[2:]); return [hex(int.from_bytes(b[i:i + 32], 'big')) for i in range(0, len(b), 32)]
    out['tx1_sync'] = {'status': res[0]['status'], 'returnData': res[0]['returnData']}
    out['tx2_exttload'] = {'status': res[1]['status'], 'words': words(res[1]['returnData'])}
    for k, n in ((2, 'tx3_unlock_settle'), (3, 'tx4_control_same_tx')):
        rd = res[k]['returnData']; rec = P.parse(bytes.fromhex(rd[2:]))
        out[n] = {'status': res[k]['status'], 'records': [[ok, d.hex()] for ok, d in rec], 'error': res[k].get('error')}
    t2 = out['tx2_exttload']['words']
    out['verdict'] = {'nextTxSeesZero': t2[-2:] == ['0x0', '0x0'],
                      'controlSeesSync': [d for ok, d in out['tx4_control_same_tx']['records']][1:3] == [T[2:].rjust(64, '0'), '1234'.rjust(64, '0')]}
except Exception as e:
    out['error'] = str(e)[:400]
try: out['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [])
except Exception as e: out['clientVersionAfter'] = 'ERR ' + str(e)[:200]
json.dump(out, open(f'out/stalesync-{label}.json', 'w'), indent=1)
print(label, out.get('clientVersionBefore'), out.get('error') or (out['tx2_exttload'], out['tx3_unlock_settle'], out['tx4_control_same_tx'], out['verdict']))
