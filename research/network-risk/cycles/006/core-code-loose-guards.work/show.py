import sys, json, os
from lib import *
def dump(hexdata, indent=''):
    lines = []
    for i, (ok, d) in enumerate(records(hexdata)):
        if ok == '?': lines.append('%s%2d ?? %s' % (indent, i, d[:80])); continue
        # nested: an unlock that returned ABI bytes, or reverted with raw records
        nested = None
        if ok and len(d) > 128 and int(d[:64], 16) == 0x20:
            n = int(d[64:128], 16); nested = d[128:128 + 2 * n]
        elif not ok and len(d) >= 128 and int(d[:64], 16) in (0, 1) and int(d[64:128], 16) < 0x10000 and len(d) % 64 == 0 and d[:8] not in ERR:
            nested = d
        if nested is not None:
            lines.append('%s%2d %s unlock, inner records:' % (indent, i, 'ok' if ok else 'REVERT'))
            lines += dump(nested, indent + '      ')
        else: lines.append('%s%2d %s' % (indent, i, short(ok, d)))
    return lines
if __name__ == '__main__':
    cid = int(sys.argv[1]); o = json.load(open(os.path.join(HERE, 'raw', 'tests_%d.json' % cid)))
    for k in sys.argv[2:] or [k for k in o if k.split('_')[0] in ('proxy', 'designator', 'real')]:
        r = o[k]; print('==', cid, k)
        if 'result' in r: print('\n'.join(dump(r['result'])))
        else: print('  ', json.dumps(r)[:300])
