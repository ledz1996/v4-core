# Tempo: TIP-20 tokens are precompiles without a selector table in code. The function list of the published interface (as in
# cycle 6, tempo.py) is run through the holder trials for the priced currencies the cycle 6 sweep did not cover.
import json, os, re, shutil
from base import *
import holder
SIGS = ['mint(address,uint256)', 'burn(uint256)', 'burnBlocked(address,uint256)', 'burnAt(address,uint256)', 'mintWithMemo(address,uint256,bytes32)', 'burnWithMemo(uint256,bytes32)',
        'transferWithMemo(address,uint256,bytes32)', 'transferFromWithMemo(address,address,uint256,bytes32)', 'transferFrom(address,address,uint256)', 'changeTransferPolicyId(uint64)',
        'setSupplyCap(uint256)', 'pause()', 'unpause()', 'setNextQuoteToken(address)', 'completeQuoteTokenUpdate()', 'permit(address,address,uint256,uint256,uint8,bytes32,bytes32)',
        'distributeReward(uint256)', 'setRewardRecipient(address)', 'claimRewards()', 'setLogoURI(string)', 'grantRole(bytes32,address)', 'revokeRole(bytes32,address)', 'renounceRole(bytes32)',
        'setRoleAdmin(bytes32,bytes32)', 'approve(address,uint256)', 'transfer(address,uint256)', 'startReward(uint256,uint128)', 'cancelReward(uint64)', 'finalizeStreams()']
for s in SIGS: holder.SIG[sel(s)[2:]] = [s]
holder.TRIG = re.compile('.')
cid = 4217
fn = os.path.join(RAW7, 'sels_%d.json.gz' % cid); S = jz(fn); shutil.copy(fn, fn + '.main')
for t in S: S[t]['sels'] = [sel(s)[2:] for s in SIGS]
try:
    wz(fn, S); holder.run(cid, minusd=0.0)
finally: shutil.move(fn + '.main', fn)
