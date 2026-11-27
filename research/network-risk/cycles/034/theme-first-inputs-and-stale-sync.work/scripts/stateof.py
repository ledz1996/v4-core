"""Read slot0 and liquidity (extsload, pools mapping slot 6, src/libraries/StateLibrary.sol layout) for the pool keys in
out/pools-<label>-keys.json and write out/pools-<label>.json for refine.py. Usage: python3 stateof.py <label> <url> <pm>"""
import sys, json, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak, rpc
label, url, pm = sys.argv[1:4]
d = json.load(open(f'out/pools-{label}-keys.json')); SEL = keccak(b'extsload(bytes32)')[:4]
def ext(slot):
    for k in range(5):
        try: return int(rpc(url, 'eth_call', [{'to': pm, 'data': '0x' + SEL.hex() + slot.to_bytes(32, 'big').hex()}, 'latest'], timeout=60), 16)
        except Exception as e: err = e; time.sleep(2 * (k + 1))
    raise err
d['clientVersionBefore'] = rpc(url, 'web3_clientVersion', [])
for pid, p in d['pools'].items():
    base = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
    s0 = ext(base); p['liquidity'] = ext(base + 3) & ((1 << 128) - 1); p['sqrtPriceX96'] = s0 & ((1 << 160) - 1)
    t = (s0 >> 160) & 0xffffff; p['tick'] = t - (1 << 24) if t >= 1 << 23 else t
d['clientVersionAfter'] = rpc(url, 'web3_clientVersion', [])
json.dump(d, open(f'out/pools-{label}.json', 'w'), indent=1); print(label, d['clientVersionBefore'], len(d['pools']))
