import json, os, sys, glob
from lib import *
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
def load(cid):
    o = json.load(open(os.path.join(HERE, 'raw', 'logs_%d.json' % cid)))
    ops = {}; sp = {}
    for l in sorted(o['logs'], key=lambda l: l['b']):
        t = l['t']; ow = '0x' + t[1][-40:]; x = '0x' + t[2][-40:]
        if t[0] == OP:
            ops.setdefault(x, {})[ow] = int(l['d'], 16)
        elif t[0] == AP:
            sp.setdefault(x, {}).setdefault(ow, {})[int(t[3], 16)] = int(l['d'], 16)
    return o, ops, sp
if __name__ == '__main__':
    for f in sorted(glob.glob(os.path.join(HERE, 'raw', 'logs_*.json'))):
        cid = int(f.split('_')[-1].split('.')[0])
        o, ops, sp = load(cid)
        print('==', cid, net(cid)['name'], 'logs', len(o['logs']), 'range', o['fromBlock'], o['toBlock'], 'fail', (o.get('stats') or {}).get('fail'), 'done' if 'done' not in o else 'windows %d' % len(o['done']))
        print('  operators', len(ops), 'spenders', len(sp))
        for x, m in sorted(ops.items(), key=lambda kv: -len(kv[1]))[:12]:
            print('   op', x, 'owners', len(m), 'still set per logs', sum(1 for v in m.values() if v))
        for x, m in sorted(sp.items(), key=lambda kv: -len(kv[1]))[:12]:
            print('   sp', x, 'owners', len(m), 'ids', len({i for mm in m.values() for i in mm}), 'nonzero last', sum(1 for mm in m.values() for v in mm.values() if v))
