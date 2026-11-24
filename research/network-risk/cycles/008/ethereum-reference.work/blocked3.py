import json; from lib import *
U='https://mainnet.gateway.tenderly.co'; PM='0x000000000004444c5dc75cB358380D2e3dE08A90'
TOK={'yUSD':'0x19ebd191f7a24ece672ba13a302212b5ef7f35cb','yETH':'0x8464f6ecae1ea58ec816c13f964030eab8ec123a','xSolvBTC':'0xd9d920aa40f578ab794426f5c90f6c731d159def'}
T0='0x'+keccak256(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
SV='0x7ffe42c4a5deea5b0fec41c94c136cf115597227'
for s in ['blackListUsers(address[])','blacklistUsers(address[])','addBlackListUsers(address[])','blacklist(address[])','blackList(address[])','addToBlacklist(address[])','setBlacklist(address[])','blacklistAccounts(address[])','addBlacklist(address[])']:
    print(s, sel(s))
for s in ['Blacklisted(address,address)','BlackListed(address,address)','Blacklist(address,address)','BlacklistAdded(address)','AddedToBlacklist(address)','BlackListAdded(address,address)']:
    print(s, keccak256(s.encode()).hex()[:16])
for a in ['0x10472f91f67c49260bdd65f016ea0757bb1fc91e','0x9efec24b767b44a46cf16e8aead9624d129a56d1','0x944416e5df03ee4c14ec44c01495005564e6b07e']:
    c=rpc(U,'eth_getCode',[a,'latest'])['result']; print(a,'code',len(c)//2-1,c[:60])
out={}
for n,t in TOK.items():
    bal=int(rpc(U,'eth_call',[{'to':t,'data':'0x'+cd('balanceOf(address)',PM)},'latest'])['result'],16)
    dec=int(rpc(U,'eth_call',[{'to':t,'data':'0x'+sel('decimals()')},'latest'])['result'],16)
    rows=[]
    for pos in (2,3):
        topics=[T0,None,None,None]; topics[pos]='0x'+w(t)
        r=rpc(U,'eth_getLogs',[{'address':PM,'topics':topics,'fromBlock':hex(21688329),'toBlock':'latest'}],timeout=90)
        for l in r['result']:
            d=bytes.fromhex(l['data'][2:])
            liq=int(rpc(U,'eth_call',[{'to':SV,'data':'0x'+cd('getLiquidity(bytes32)',l['topics'][1])},'latest'])['result'],16)
            rows.append({'id':l['topics'][1],'c0':'0x'+l['topics'][2][26:],'c1':'0x'+l['topics'][3][26:],'fee':int.from_bytes(d[0:32],'big'),'hooks':'0x'+d[76:96].hex(),'block':int(l['blockNumber'],16),'activeLiquidity':liq})
    out[n]={'token':t,'balance':bal/10**dec,'pools':rows}
    print(n,'PM balance',bal/10**dec,'pools',len(rows))
    for x in rows: print('   ',x)
json.dump(out,open('raw_blocked_pools.json','w'),indent=0)
