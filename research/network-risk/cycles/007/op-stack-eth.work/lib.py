import json, urllib.request, os, ssl, time
RPC={10:'https://mainnet.optimism.io',8453:'https://mainnet.base.org/',130:'https://mainnet.unichain.org',7777777:'https://rpc.zora.energy/',480:'https://worldchain-mainnet.g.alchemy.com/public',57073:'https://rpc-gel.inkonchain.com',1868:'https://rpc.soneium.org'}
PM={10:'0x9a13f98cb987694c9f086b1f5eb990eea8264ec3',8453:'0x498581ff718922c3f8e6a244956af099b2652b2b',130:'0x1f98400000000000000000000000000000000004',7777777:'0x0575338e4c17006ae181b47900a84404247ca30f',480:'0xb1860d529182ac3bc1f51fa2abd56662b7d13f33',57073:'0x360e68faccca8ca495c1b759fd9eee466db9fb32',1868:'0x360e68faccca8ca495c1b759fd9eee466db9fb32'}
def rpc(url, method, params, timeout=40):
    if isinstance(url,int): url=RPC[url]
    req=urllib.request.Request(url, data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(), headers={'Content-Type':'application/json','User-Agent':'research-client/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        try: body=e.read().decode()[:500]
        except Exception: body=''
        return {'error':{'message':repr(e)+' '+body}}
def call(chain,to,data,frm=None,value=None,override=None,block='latest',gas=None):
    tx={'to':to,'data':data}
    if frm: tx['from']=frm
    if value is not None: tx['value']=hex(value)
    if gas: tx['gas']=hex(gas)
    p=[tx,block]
    if override: p.append(override)
    return rpc(chain,'eth_call',p)
