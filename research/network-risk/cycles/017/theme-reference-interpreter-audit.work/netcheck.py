"""The semantic cases of semtest.py on all 21 networks (eth_call with state overrides at the latest block), each compared
with the corrected reference pyevm_tx17.py. modexp with a 1025 byte length is reported per network as an Osaka marker
and judged against the reference with and without the EIP-7823 bound. Read-only. usage: python3 netcheck.py > out/netcheck.json"""
import sys, json, os, concurrent.futures as cf
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import semtest as T
NETS = json.load(open(os.path.join(T.NR, 'state', 'networks.json')))['networks']
NAMES = ['call_value_returndata', 'static_nested', 'returndatacopy_bounds', 'delegatecall_context', 'rollback_revert', 'rollback_invalid',
         'rollback_rdoob', 'stack_overflow', 'memory_zero_length', 'mcopy_overlap', 'jumps', 'signed_edges', 'calldata_offsets',
         'extcodesize', 'extcodehash', 'call_delegated', 'precompile_0x1_128', 'precompile_0x4_128', 'precompile_0x5_modexp',
         'precompile_modexp_1025', 'ecrecover_short', 'callcode']
CASES = {c['name']: c for c in T.CASES if c['name'] in NAMES}

def local(c, osaka):
    r = T.run_local(T.P4, c) if not osaka else None
    if osaka:
        codes = dict(c['codes']); bal = dict(c['balances']); bal.setdefault(T.FROM, 10 ** 18)
        w = T.P4.World(codes, bal); w.ctx = {'osaka': True}
        try: ok, ret = w.call(T.FROM, T.A, c['value'], c['data'], False, 0); r = {'ok': ok, 'ret': ret.hex()}
        except Exception as e: r = {'raise': str(e)}
    else:
        codes = dict(c['codes']); bal = dict(c['balances']); bal.setdefault(T.FROM, 10 ** 18)
        w = T.P4.World(codes, bal); w.ctx = {'osaka': False}
        try: ok, ret = w.call(T.FROM, T.A, c['value'], c['data'], False, 0); r = {'ok': ok, 'ret': ret.hex()}
        except Exception as e: r = {'raise': str(e)}
    return r

def net(n):
    T.RPC = n['rpc'] if 'rpc' in n else n.get('rpcUrl')
    out = {'chainId': n['chainId'], 'name': n['name'], 'cases': {}}
    try:
        blk = T.rpc('eth_getBlockByNumber', ['latest', False])['result']['number']; out['block'] = int(blk, 16)
    except Exception as e: out['error'] = str(e)[:120]; return out
    for nm, c in CASES.items():
        # a state override on a precompile address turns the precompile off on geth-family endpoints (bor, Nitro, BSC geth):
        # precompile accounts keep their real balance here, read with eth_getBalance, and the reference is given that balance
        c = dict(c); c['balances'] = dict(c['balances'])
        try:
            for a in [a for a in c['balances'] if 0 < a < 0x12 or a == 0x100]:
                rb = {}
                for _ in range(4):
                    rb = T.rpc('eth_getBalance', ['0x%040x' % a, blk])
                    if 'result' in rb: break
                    __import__('time').sleep(2)
                c['balances'][a] = int(rb['result'], 16); c.setdefault('keep', set()).add(a)
        except Exception as e: out['cases'][nm] = {'error': 'balance read: ' + str(e)[:100]}; continue
        try: ch = T.run_chain(c, blk)
        except Exception as e: out['cases'][nm] = {'error': str(e)[:120]}; continue
        a, b = local(c, False), local(c, True)
        same = lambda r: 'raise' not in r and r['ok'] == ch['ok'] and r['ret'] == ch['ret']
        out['cases'][nm] = {'chainOk': ch['ok'], 'err': ch.get('error'), 'refPreOsaka': same(a), 'refOsaka': same(b),
                            'chainRet': ch['ret'][:200] if not (same(a) or same(b)) else None}
    return out

if __name__ == '__main__':
    res = []
    with cf.ThreadPoolExecutor(1) as ex:  # semtest.RPC is a module global: one network at a time
        for n in NETS: r = net(n); res.append(r); print(n['chainId'], n['name'], {k: ('=' if v.get('refPreOsaka') or v.get('refOsaka') else ('ERR' if 'error' in v or v.get('err') else 'DIFF')) for k, v in r['cases'].items()} if 'cases' in r else r, file=sys.stderr, flush=True)
    json.dump(res, sys.stdout, indent=1)
