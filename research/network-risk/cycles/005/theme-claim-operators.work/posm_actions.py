# Behaviour check of the PositionManager action table on all 21 networks (eth_call from an unrelated account, nothing sent).
import json, os, hashlib
from lib import *
from abi2 import calldata, enc_tuple
from state import url
MAXU = (1 << 256) - 1
def ml(acts):
    return calldata('modifyLiquidities(bytes,uint256)', [enc_tuple(['bytes', 'bytes[]'], [bytes(a for a, _ in acts), [p for _, p in acts]]), MAXU])
A = '0x00000000000000000000000000000000a77ac4e5'
names = {0:'INCREASE_LIQUIDITY',1:'DECREASE_LIQUIDITY',2:'MINT_POSITION',3:'BURN_POSITION',4:'INCREASE_LIQUIDITY_FROM_DELTAS',5:'MINT_POSITION_FROM_DELTAS',6:'SWAP_EXACT_IN_SINGLE',7:'SWAP_EXACT_IN',8:'SWAP_EXACT_OUT_SINGLE',9:'SWAP_EXACT_OUT',10:'DONATE',11:'SETTLE',12:'SETTLE_ALL',13:'SETTLE_PAIR',14:'TAKE',15:'TAKE_ALL',16:'TAKE_PORTION',17:'TAKE_PAIR',18:'CLOSE_CURRENCY',19:'CLEAR_OR_TAKE',20:'SWEEP',21:'WRAP',22:'UNWRAP',23:'MINT_6909',24:'BURN_6909'}
ref = None; out = {}
for n in NETS:
    cid = n['chainId']; u = url(cid); posm = n['contracts']['PositionManager']; row = {}
    try:
        code = rpc(u, 'eth_getCode', [posm, 'latest']); row['codeLen'] = len(code) // 2 - 1
        sup = []; uns = []
        for a in range(0, 26):
            # 12 zero words as parameters: enough for every decoder to read its static head
            try:
                rpc(u, 'eth_call', [{'from': A, 'to': posm, 'data': ml([(a, bytes(32 * 12))])}, 'latest'], tries=2); sup.append(a)
            except Exception as e:
                s = str(e)
                if '5cda29d7' in s: uns.append(a)
                else: sup.append(a)
        row['handled'] = sup; row['unsupported'] = uns
    except Exception as e: row['err'] = str(e)[:100]
    out[cid] = row
    print(cid, n['name'], row.get('codeLen'), 'unsupported:', [names.get(a, a) for a in row.get('unsupported', [])], 'handled:', row.get('handled'), row.get('err', ''), flush=True)
json.dump(out, open(os.path.join(HERE, 'raw', 'posm_actions.json'), 'w'))
