"""Cycle 39 (L-1356): what GAS returns and what CALL(gas(), ...) forwards, on mainnet (Osaka) and Sepolia (Amsterdam,
EIP-8037 reservoir), by eth_call with state override. Probes:
  p_gas   : GAS at the first opcode
  p_call  : CALL(GAS, child) where child returns GAS at its first opcode (what call(gas(), ...) at
            src/types/Currency.sol:48, :73 and src/libraries/Hooks.sol:134 hands the callee)
  p_sstore: CALL(GAS, child2) where child2 writes a new slot then returns GAS (state gas from reservoir or gas_left)
usage: python3 probe.py out.json url..."""
import json, sys, urllib.request
CHILD = '0x' + '00' * 19 + 'c1'
CHILD2 = '0x' + '00' * 19 + 'c2'
P = '0x' + '00' * 19 + 'aa'
ret_gas = '5a5f5260205ff3'                       # GAS PUSH0 MSTORE PUSH1 32 PUSH0 RETURN
sstore_then_gas = '60015f55' + ret_gas            # PUSH1 1 PUSH0 SSTORE ; then return GAS
def caller(child):
    # PUSH1 32 PUSH0 PUSH0 PUSH0 PUSH0 PUSH20 child GAS CALL POP PUSH1 32 PUSH0 RETURN
    return '60205f5f5f5f73' + child[2:] + '5af15060205ff3'
def rpc(url, m, p):
    r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'research-client'})
    import time
    for k in range(6):
        try:
            return json.load(urllib.request.urlopen(r, timeout=60))
        except Exception as e:  # rate limits: wait and retry, then report the error as the answer
            last = e; time.sleep(3 * (k + 1))
    return {'error': str(last)}
out = {}
for url in sys.argv[2:]:
    cv = rpc(url, 'web3_clientVersion', []).get('result')
    rows = []
    for gas in (100_000, 1_000_000, 16_000_000, 16_777_216, 30_000_000, 60_000_000):
        row = {'gas': gas}
        for name, code in (('p_gas', ret_gas), ('p_call', caller(CHILD)), ('p_sstore', caller(CHILD2))):
            ov = {P: {'code': '0x' + code}, CHILD: {'code': '0x' + ret_gas}, CHILD2: {'code': '0x' + sstore_then_gas}}
            r = rpc(url, 'eth_call', [{'from': '0x' + '00' * 19 + '01', 'to': P, 'gas': hex(gas)}, 'latest', ov])
            row[name] = int(r['result'], 16) if 'result' in r else r.get('error')
        rows.append(row)
    out[url] = {'clientVersion': cv, 'rows': rows}
    print(url, cv)
    for r in rows: print('  ', r)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
