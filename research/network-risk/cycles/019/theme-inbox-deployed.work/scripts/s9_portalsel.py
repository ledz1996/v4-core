import json,glob,os
from keccak import keccak256
from s3_selectors import selectors
names={}
for a in ['0x03863ab7f64b733cff85c8ff44a86601c568ca70','0xe89f13c5ee4033b2d3cd76c9d6958efbfe26d3c2','0xa0fefc3a457f6a1ae2d81fc172d6de090a9f4033']:
    for e in json.load(open(f'../dl/sourcify/1_{a}.json'))['abi']:
        if e['type']=='function':
            def t(x):
                if x['type'].startswith('tuple'): return '('+','.join(t(c) for c in x['components'])+')'+x['type'][5:]
                return x['type']
            sig=e['name']+'('+','.join(t(x) for x in e['inputs'])+')'
            names[keccak256(sig.encode()).hex()[:8]]=sig
extra=['ethLockbox()','migrateLiquidity()','migrateToSuperRoots(address,address)','proxyAdminOwner()','superRootsActive()','upgrade(address,address)','initialize(address,address)','donateETH()','anchorStateRegistry()','disputeGameFactory()','systemConfig()','superchainConfig()','respectedGameType()','guardian()','paused()','version()','depositTransaction(address,uint256,uint64,bool,bytes)','proveWithdrawalTransaction((uint256,address,address,uint256,uint256,bytes),uint256,(bytes32,bytes32,bytes32,bytes32),bytes[])','finalizeWithdrawalTransaction((uint256,address,address,uint256,uint256,bytes))','finalizeWithdrawalTransactionExternalProof((uint256,address,address,uint256,uint256,bytes),address)','checkWithdrawal(bytes32,address)','numProofSubmitters(bytes32)','proofMaturityDelaySeconds()','disputeGameFinalityDelaySeconds()','minimumGasLimit(uint64)','params()','l2Sender()','reinitializerValue()','initVersion()','proxyAdmin()','setGasPayingToken(address,uint8,bytes32,bytes32)','depositERC20Transaction(address,uint256,uint256,uint64,bool,bytes)','gasPayingToken()','balance()','isGasPayingToken()','upgrade(address)','initialize(address,address,address)','initialize(address,address)','lastProofTimestamp()','feature()']
for s in extra: names.setdefault(keccak256(s.encode()).hex()[:8],s)
code={}
for f in sorted(glob.glob('../raw/code/portal_*.hex')):
    s=selectors(open(f).read().strip())
    c=open(f).read().strip()
    # also PUSH3 selectors with a leading zero byte
    print(os.path.basename(f),len(s))
    print('   ',sorted(names.get(x,'?'+x) for x in s))
