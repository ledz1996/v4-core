"""Rerun tools/opdiff/replay.py's replay() for the one Arc swap it could not reproduce, with tick spacing 90 (read from
the PositionManager poolKeys entry of the pool) added to its candidate list. Read-only eth_call."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
import replay as R
from evm import networks
R.SPACINGS = [90]
s = json.load(open(sys.argv[1])); found = []
def walk(o):
    if isinstance(o, dict):
        if str(o.get('tx', '')).startswith('0x1337adbb') and 'p0' in o: found.append(o); return
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(s)
url = [n[2] for n in networks() if n[0] == 5042][0]
ch = R.Chain(url, '0x8366a39CC670B4001A1121B8F6A443A643e40951')
res = R.replay(ch, found[0]); res['tx'] = found[0]['tx']; print(res)
json.dump(res, open(sys.argv[2], 'w'))
