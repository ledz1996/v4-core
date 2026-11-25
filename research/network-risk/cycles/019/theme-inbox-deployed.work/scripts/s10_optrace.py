import json
from rpc import *
from keccak import keccak256
def sel(s): return '0x'+keccak256(s.encode()).hex()[:8]
def w(x): return hex(x)[2:].rjust(64,'0')
D='https://eth.drpc.org'
TD='0x'+keccak256(b'TransactionDeposited(address,address,uint256,bytes)').hex()
OFF=0x1111000000000000000000000000000000001111; M=1<<160
portals=json.load(open('../raw/portals.json'))
nets={x['chainId']:x for x in json.load(open('../../../../state/networks.json'))['networks']}
bridges={10:'0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1',8453:'0x3154Cf16ccdb4C6d922629664174b904d80F2C35',130:'0x81014F44b0a345033bB2b3B21C7a1A308B35fEeA',7777777:'0x3e2Ea9B92B7E48A52296fD261dc26fd995284631',480:'0x470458C91978D2d929704489Ad730DC3E3001113',57073:'0x88FF1e5b602916615391F55854588EFcBB7663f0',1868:'0xeb9bf100225c214Efc3E7C651ebbaDcF85177607',42220:'0x9C4955b92F34148dbcfDCD82e9c9eCe5CF2badfe'}
def logs(c,acc):
    for l in c.get('logs',[]): acc.append(l)
    for x in c.get('calls',[]): logs(x,acc)
    return acc
def tdfrom(r):
    if not isinstance(r,dict) or 'input' not in r: return ('ERR',str(r)[:160])
    L=[l for l in logs(r,[]) if l['topics'][0]==TD]
    return [('0x'+l['topics'][1][-40:],'0x'+l['topics'][2][-40:]) for l in L] or ('noTD',r.get('error'),r.get('revertReason'))
out={'client_start':rpc1(D,'web3_clientVersion',[])}
EOA='0x000000000000000000000000000000000000dEaD'
for cid in [10,8453,130,7777777,480,57073,1868,42220,196]:
    p=portals[str(cid)]['portal']; pm=nets[cid]['poolManager']
    dep=sel('depositTransaction(address,uint256,uint64,bool,bytes)')+w(0xbeef)+w(0)+w(100000)+w(0)+w(0xa0)+w(0)
    d={'portal':p,'poolManager':pm}
    d['eoaCaller']=tdfrom(rpc1(D,'debug_traceCall',[{'from':EOA,'to':p,'data':dep},'latest',{'tracer':'callTracer','tracerConfig':{'withLog':True}}]))
    d['fromEqualsPMaddrOnL1']=tdfrom(rpc1(D,'debug_traceCall',[{'from':pm,'to':p,'data':dep},'latest',{'tracer':'callTracer','tracerConfig':{'withLog':True}}]))
    if cid in bridges:
        bd=sel('bridgeETH(uint32,bytes)')+w(200000)+w(0x40)+w(0)
        d['viaL1StandardBridge']=tdfrom(rpc1(D,'debug_traceCall',[{'from':EOA,'to':bridges[cid],'data':bd},'latest',{'tracer':'callTracer','tracerConfig':{'withLog':True}}]))
    pre='0x%040x'%((int(pm,16)-OFF)%M)
    d['preimage']=pre
    d['preimage_code']=rpc(ETH,'eth_getCode',[pre,'latest']); d['preimage_nonce']=rpc(ETH,'eth_getTransactionCount',[pre,'latest'])
    d['pmAddrOnL1_codeLen']=(len(rpc(ETH,'eth_getCode',[pm,'latest']))-2)//2; d['pmAddrOnL1_nonce']=rpc(ETH,'eth_getTransactionCount',[pm,'latest'])
    out[cid]=d; print(cid,json.dumps(d))
out['client_end']=rpc1(D,'web3_clientVersion',[])
json.dump(out,open('../raw/op_deposit_traces.json','w'),indent=1)
