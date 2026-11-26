"""Cycle 26 variant of cycles/024/established-l1.work/run_pin.py for lead L-1084.
Every eth_call of an opdiff tool is sent to PIN_URL as a JSON-RPC batch
[web3_clientVersion, eth_call, web3_clientVersion] and repeated until every build in
$BUILDS (comma separated commit prefixes) has answered it with the same build string on
both brackets, up to $MAXTRY attempts. The answers of all builds must be byte equal; any
difference is written in full to $DIFFLOG. The tool then compares the common answer with
its reference. Read-only.
Usage: python3 -I run_pin5.py <tool.py> <args...>"""
import sys, os, runpy, json, urllib.request, collections, atexit, time
T = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, T)
import evm
URL = os.environ['PIN_URL']
BUILDS = os.environ['BUILDS'].split(',')
MAXTRY = int(os.environ.get('MAXTRY', '40'))
evm.networks = lambda path=None: [(137, 'Polygon pinned x5', URL)]
stats = {'calls': 0, 'perBuild': collections.Counter(), 'incomplete': 0, 'missingBuilds': collections.Counter(),
         'otherTags': collections.Counter(), 'differences': 0, 'challenge': 0}
orig = evm.rpc


def rpc(url, method, params, timeout=90):
    if url != URL or method != 'eth_call':
        return orig(url, method, params, timeout)
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                       {'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params},
                       {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]).encode()
    seen = {}
    for attempt in range(MAXTRY):
        req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=evm._ctx) as r:
                raw = r.read()
            j = json.loads(raw)
        except Exception as e:  # noqa  (a challenge page is not JSON; it is recorded, not worked around)
            stats['challenge'] += 1; time.sleep(5); continue
        d = {x['id']: x for x in j}
        t1, t3 = d[1].get('result', 'ERR'), d[3].get('result', 'ERR')
        b = next((x for x in BUILDS if x in t1), None)
        if t1 != t3 or b is None:
            stats['otherTags'][t1 if t1 == t3 else t1 + ' | ' + t3] += 1; continue
        ans = d[2].get('result') if 'error' not in d[2] else 'ERROR ' + json.dumps(d[2]['error'])[:300]
        seen.setdefault(b, ans)
        if len(seen) == len(BUILDS): break
    stats['calls'] += 1
    for b in seen: stats['perBuild'][b] += 1
    if len(seen) < len(BUILDS):
        stats['incomplete'] += 1
        for b in BUILDS:
            if b not in seen: stats['missingBuilds'][b] += 1
    vals = set(seen.values())
    if len(vals) > 1:
        stats['differences'] += 1
        open(os.environ.get('DIFFLOG', 'pin5-diff.jsonl'), 'a').write(json.dumps({'params': params, 'answers': seen}) + '\n')
    if not seen:
        raise RuntimeError('no pinned build answered')
    first = next(iter(seen.values()))
    if first.startswith('ERROR'):
        raise RuntimeError(first)
    return first


evm.rpc = rpc
atexit.register(lambda: open(os.environ.get('TAGLOG', 'pin5-tags.log'), 'a').write(json.dumps({'tool': sys.argv[0], 'builds': BUILDS, **stats}) + '\n'))
tool = sys.argv[1]
sys.argv = [os.path.join(T, tool)] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name='__main__')
