"""Replay the Polygon multi-step samples of a swaps.json one at a time, printing each
result as it finishes, with state from the Tenderly public gateway. Read-only.
Usage: python3 -I replay_one.py <swaps.json> <out.json> [spacings.json]
With a spacings file (pool id -> tick spacing from the Initialize log) only that spacing is tried."""
import sys, json, time
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import replay as R
src = json.load(open(sys.argv[1]))
ch = R.Chain('https://polygon.gateway.tenderly.co', '0x67366782805870060151383f4bbff9dab53e5cd6')
out = []
SP = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
import signal
def _alarm(*a): raise TimeoutError('time limit 600 s')
signal.signal(signal.SIGALRM, _alarm)
for r in src['results']:
    if r['chainId'] != 137: continue
    for smp in r.get('multiSamples', []) + r.get('otherSamples', []):
        t = time.time()
        if smp['pool'] in SP: R.SPACINGS = [SP[smp['pool']]]
        signal.alarm(600)
        try: res = R.replay(ch, smp)
        except Exception as e: res = {'ok': False, 'why': str(e)[:120]}
        signal.alarm(0)
        res.update({'tx': smp['tx'], 'secs': round(time.time() - t, 1)}); out.append(res)
        print(json.dumps(res), flush=True)
        json.dump({'results': out}, open(sys.argv[2], 'w'), indent=1)
