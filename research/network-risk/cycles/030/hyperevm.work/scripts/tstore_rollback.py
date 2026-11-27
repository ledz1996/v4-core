"""Transient storage journal vectors by eth_call with code overrides. Usage: tstore_rollback.py <out.json> <url>..."""
import sys, json, urllib.request
X = '0x00000000000000000000000000000000000c0de1'; Y = '0x00000000000000000000000000000000000c0de2'
YR = '0x00000000000000000000000000000000000c0de3'; Z = '0x00000000000000000000000000000000000c0de4'
SS = '0x00000000000000000000000000000000000c0de5'
def a(x): return '73' + x[2:]
def dcall(t): return '6000600060006000' + a(t) + '5af4'  # retLen retOff argsLen argsOff addr gas DELEGATECALL
def call(t): return '60006000600060006000' + a(t) + '5af1'
def scall(t): return '6000600060006000' + a(t) + '5afa'
RET_T1 = '60015c60005260206000f3'  # TLOAD(1) return
RET_TOP = '60005260206000f3'
code_y_ok = '0x600760015d00'
code_y_rev = '0x600760015d60006000fd'
code_z = '0x' + dcall(Y) + '50' + '60006000fd'  # delegatecall Y ok then revert
code_ss = '0x' + '600960025d' + '60025c60005260206000f3'  # tstore(2,9) tload(2) return
cases = {
 'dcall_revert_rolls_back': ('0x' + dcall(YR) + '50' + RET_T1, 0),
 'dcall_ok_persists': ('0x' + dcall(Y) + '50' + RET_T1, 7),
 'prior_value_kept_after_revert': ('0x600560015d' + dcall(YR) + '50' + RET_T1, 5),
 'nested_outer_revert_rolls_inner': ('0x600560015d' + dcall(Z) + '50' + RET_T1, 5),
 'tstore_in_staticcall_fails': ('0x' + scall(Y) + RET_TOP, 0),
 'tload_in_staticcall_ok': ('0x600560015d' + '6020600060006000' + a(X) + '5afa' + '50' + '60005160005260206000f3', None),
 'call_ok_other_account_isolated': ('0x' + call(Y) + '50' + RET_T1, 0),
 'tstore_then_tload_same_frame_callee': ('0x' + '6020600060006000' + '6000' + a(SS) + '5af1' + '50' + '60005160005260206000f3', 9),
 'revert_after_return_data_tstore_gone': ('0x' + call(YR) + '50' + '6000' + a(YR) + '5a' + '50' + '50' + RET_T1, 0),
}
def rpc(url, m, p):
    r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=60))
out = {}
for url in sys.argv[2:]:
    out[url] = {'clientVersion': rpc(url, 'web3_clientVersion', [])['result']}
    for name, (code, exp) in cases.items():
        ov = {X: {'code': code}, Y: {'code': code_y_ok}, YR: {'code': code_y_rev}, Z: {'code': code_z}, SS: {'code': code_ss}}
        r = rpc(url, 'eth_call', [{'to': X, 'gas': '0x989680'}, 'latest', ov])
        got = int(r['result'], 16) if r.get('result') not in (None, '0x') else r
        out[url][name] = {'got': got, 'expected': exp, 'ok': exp is None or got == exp}
    print(url, out[url]['clientVersion'], sum(v['ok'] for k, v in out[url].items() if k != 'clientVersion'), '/', len(cases), {k: v['got'] for k, v in out[url].items() if k != 'clientVersion'})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
