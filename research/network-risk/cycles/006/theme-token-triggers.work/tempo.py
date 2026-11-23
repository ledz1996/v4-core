# Tempo: TIP-20 tokens are precompiles and carry no selector table in code, so the function list of the published interface
# (rustdocs.tempo.xyz, tempo_precompiles::tip20::ITIP20) is used for the step 2 trials.
import json, gzip, os, shutil
from base import *
import sweep, slots
SIGS = ['mint(address,uint256)', 'burn(uint256)', 'burnBlocked(address,uint256)', 'burnAt(address,uint256)', 'mintWithMemo(address,uint256,bytes32)', 'burnWithMemo(uint256,bytes32)',
        'transferWithMemo(address,uint256,bytes32)', 'transferFromWithMemo(address,address,uint256,bytes32)', 'transferFrom(address,address,uint256)', 'changeTransferPolicyId(uint64)',
        'setSupplyCap(uint256)', 'pause()', 'unpause()', 'setNextQuoteToken(address)', 'completeQuoteTokenUpdate()', 'permit(address,address,uint256,uint256,uint8,bytes32,bytes32)',
        'distributeReward(uint256)', 'setRewardRecipient(address)', 'claimRewards()', 'setLogoURI(string)', 'grantRole(bytes32,address)', 'revokeRole(bytes32,address)', 'renounceRole(bytes32)',
        'setRoleAdmin(bytes32,bytes32)', 'approve(address,uint256)', 'transfer(address,uint256)', 'startReward(uint256,uint128)', 'cancelReward(uint64)', 'finalizeStreams()']
for s in SIGS:
    sweep.SIG[sel(s)[2:]] = [s]
sweep.TRIG = __import__('re').compile('.')   # run the argument-free and number-only functions as well
cid = 4217
real = os.path.join(RAW6, 'discover_%d.json.gz' % cid); d = jz(real)
for t, o in d.items(): o['sels'] = [sel(s)[2:] for s in SIGS]
shutil.copy(real, real + '.main')
try:
    json.dump(d, gzip.open(real, 'wt'))
    slots.run(cid)
    sweep.run(cid, mode='A'); sweep.run(cid, mode='B')
finally:
    shutil.move(real + '.main', real)
