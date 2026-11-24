import json; from lib import *
U='https://mainnet.gateway.tenderly.co'; pm='000000000004444c5dc75cb358380d2e3de08a90'
TOK={'yUSD':'0x19ebd191f7a24ece672ba13a302212b5ef7f35cb','yETH':'0x8464f6ecae1ea58ec816c13f964030eab8ec123a','xSolvBTC':'0xd9d920aa40f578ab794426f5c90f6c731d159def'}
for b in (24283369,25518435):
    r=rpc(U,'eth_getLogs',[{'fromBlock':hex(b),'toBlock':hex(b)}],timeout=90)
    ls=r['result']; print('block',b,'logs',len(ls))
    txs=set()
    for l in ls:
        blob=(''.join(l['topics'])+l['data']).lower()
        if l['address'].lower() in TOK.values() and (pm in blob) or (pm in blob and len(l['topics'])<=2 and l['address'].lower()!='0x'+pm):
            if l['address'].lower() in [v for v in TOK.values()] or True:
                pass
        if l['address'].lower() in TOK.values() or (pm in blob and l['address'].lower() not in ('0x'+pm,)):
            if pm in blob and not l['topics'][0].startswith('0xddf252ad') and not l['topics'][0].startswith('0x8c5be1e5'):
                print(' ',l['address'],l['topics'],l['data'][:200],l['transactionHash']); txs.add(l['transactionHash'])
    for h in txs:
        t=rpc(U,'eth_getTransactionByHash',[h])['result']
        print('  TX',h,'from',t['from'],'to',t['to'],'input',t['input'][:650])
