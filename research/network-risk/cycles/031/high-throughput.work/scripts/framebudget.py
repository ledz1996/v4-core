# L-1197 probe: what a CALL sees when the callee exceeds a Rex4 per-frame budget on MegaETH.
# Read-only eth_call with state overrides. Parent calls child, returns (success, returndatasize, returndata).
import json, sys, urllib.request
RPC = sys.argv[1]; OUT = sys.argv[2]
P = '0x' + 'aa'*20
kids = {
  'stop':        '00',
  'stategrowth': '60015b6001815560010160025600',     # SSTORE(i,1) for i=1,2,... forever
  'compute':     '5b600056',                          # JUMPDEST PUSH1 0 JUMP forever
  'datalog':     '5b620100006000a0600056',            # LOG0(0,65536) forever
  'revert':      '60006000fd',
}
def parent(child, gasarg=None):
    g = '5a' if gasarg is None else '63' + '%08x' % gasarg
    return ('6000600060006000600073' + child[2:] + g + 'f1' +
            '600052' + '3d602052' + '3d60006040' + '3e' + '3d604001' + '6000f3')
res = {}
for name, code in kids.items():
    for gasarg in (None, 50_000_000):
        C = '0x' + ('%02x' % (len(res)+1))*20
        body = {"jsonrpc":"2.0","id":1,"method":"eth_call","params":[
            {"from":"0x00000000000000000000000000000000000000f1","to":P,"gas":hex(1_000_000_000)},
            "latest", {P:{"code":"0x"+parent(C, gasarg)}, C:{"code":"0x"+code}}]}
        req = urllib.request.Request(RPC, json.dumps(body).encode(), {'content-type':'application/json','user-agent':'curl/8.5.0'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:
            r = {'exc': str(e)}
        key = f'{name}/gas={gasarg}'
        out = {'raw': r}
        if 'result' in r:
            h = r['result'][2:]
            out['success'] = int(h[:64] or '0', 16); out['returndatasize'] = int(h[64:128] or '0', 16); out['returndata'] = '0x'+h[128:]
        res[key] = out
        print(key, {k:v for k,v in out.items() if k!='raw'} or r, flush=True)
json.dump(res, open(OUT,'w'), indent=1)
