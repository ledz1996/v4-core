"""Rerun, with replay2.py's full loop, every multi-step and unmatched swap sample stored by cycles 8 to 12
(otherSamples and multiSamples of every swaps*.json, opcodes/swaps.json, opcodes/swaps-deep.json).
The pool key comes from the Initialize event; the tick bitmap and ticks from the parent block plus the
ModifyLiquidity events of the pool earlier in the same block. Usage: python3 samples.py <out.json> [chainId ...]"""
import sys, os, glob, json, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replay2 as R
from endpoints import NETS, log_urls, state_urls

ROOT = '/home/user/v4-core/research/network-risk'
EXTRA_STATE = {42161: ['https://arbitrum.gateway.tenderly.co', 'https://arb1.arbitrum.io/rpc'], 43114: ['https://api.avax.network/ext/bc/C/rpc'],
               4663: ['https://robinhood.drpc.org']}


def gather():
    files = sorted(set(glob.glob(ROOT + '/cycles/00[89]/*/**/swaps*.json', recursive=True) + glob.glob(ROOT + '/cycles/01[012]/*/**/swaps*.json', recursive=True)
                       + [ROOT + '/opcodes/swaps.json', ROOT + '/opcodes/swaps-deep.json'] + glob.glob(ROOT + '/cycles/010/hyperevm.work/out/replay_archive.json.in.json')))
    seen = {}
    for f in files:
        try:
            d = json.load(open(f))
        except Exception:  # noqa
            continue
        for r in d.get('results', []):
            for kind in ('otherSamples', 'multiSamples'):
                for smp in r.get(kind, []):
                    k = (r['chainId'], smp['tx'], smp['pool'], smp['a0'], smp['a1'])
                    if k not in seen: seen[k] = {'chainId': r['chainId'], 'kind': kind[:-7], 'file': os.path.relpath(f, ROOT), **smp}
    return list(seen.values())


def main():
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    smps = [x for x in gather() if not only or x['chainId'] in only]
    print('samples', len(smps), flush=True)
    rl = {c: R.Rpc(log_urls(c)) for c in {x['chainId'] for x in smps}}
    st = {c: R.State(R.Rpc(EXTRA_STATE.get(c, state_urls(c))), NETS[c]['poolManager']) for c in rl}
    keys = {}
    for c in rl:
        kp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw', f'keys-{c}.json')
        k = json.load(open(kp)) if os.path.exists(kp) else {}
        head = int(rl[c]('eth_blockNumber', []), 16)
        try:
            keys[c] = R.find_keys(rl[c], NETS[c]['poolManager'], sorted({x['pool'] for x in smps if x['chainId'] == c}), head, k, c)
        except Exception as e:  # noqa
            print(c, 'keys failed', e); keys[c] = k
        json.dump(keys[c], open(kp.replace('keys-', 'keys-samples-'), 'w'))

    def work(x):
        c = x['chainId']; pm = NETS[c]['poolManager']
        ev = {'tx': x['tx'], 'pool': x['pool'], 'block': x['block'], 'a0': int(x['a0']), 'a1': int(x['a1']), 'p': int(x['p1']), 'liq': int(x['liq']),
              'tick': x['tick1'], 'fee': x['fee']}
        pre = (int(x['p0']), x['tick0'], int(x['liq']))
        try:
            logs = rl[c]('eth_getLogs', [{'address': pm, 'fromBlock': hex(x['block']), 'toBlock': hex(x['block']), 'topics': [[R.SWAP, R.MODIFY], x['pool']]}])
        except Exception as e:  # noqa
            return {**x, 'ok': False, 'why': 'logs not served: ' + str(e)[:80]}
        logs.sort(key=lambda y: int(y['logIndex'], 16)); mods = []; found = False
        for y in logs:
            d = y['data']
            if y['topics'][0] == R.SWAP and y['transactionHash'] == x['tx'] and R.s(R.word(d, 0)) == ev['a0'] and R.s(R.word(d, 1)) == ev['a1']:
                found = True; break
            if y['topics'][0] == R.MODIFY: mods.append((R.s24(R.word(d, 0)), R.s24(R.word(d, 1)), R.s(R.word(d, 2))))
        if not found: return {**x, 'ok': False, 'why': 'swap log not found in block'}
        key = keys[c].get(x['pool'])
        last = None
        for sp in ([key['spacing']] if key else R.SPACINGS):
            try:
                r = R.full_replay(R.PoolView(st[c], x['pool'], x['block'], sp, mods), ev, pre, 0)
            except AssertionError:
                continue
            except R.m.Revert as e:
                last = {'ok': False, 'why': 'overlay ' + str(e)}; continue
            except Exception as e:  # noqa
                return {**x, 'ok': False, 'why': 'missing archive state: ' + str(e)[:100]}
            r.update(spacing=sp, keyKnown=bool(key), modsBefore=len(mods))
            if r['ok']: return {**x, **r}
            last = last or r
        return {**x, **(last or {'ok': False, 'why': 'no spacing'}), 'keyKnown': bool(key)}

    with cf.ThreadPoolExecutor(10) as ex:
        res = list(ex.map(work, smps))
    summ = {}
    for r in res:
        a = summ.setdefault(NETS[r['chainId']]['name'], {'samples': 0, 'replayed': 0, 'aside': {}, 'unmatched': 0, 'keyKnown': 0})
        a['samples'] += 1; a['keyKnown'] += bool(r.get('keyKnown'))
        if r.get('ok'): a['replayed'] += 1
        elif 'why' in r and ('archive' in r['why'] or 'not served' in r['why'] or 'not found' in r['why']):
            w = r['why'][:30]; a['aside'][w] = a['aside'].get(w, 0) + 1
        else: a['unmatched'] += 1
    for k, v in sorted(summ.items()): print(k, v)
    json.dump({'summary': summ, 'results': res}, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
