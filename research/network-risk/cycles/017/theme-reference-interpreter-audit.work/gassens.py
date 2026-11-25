"""Sensitivity of a replay17.py rerun to the approximate GAS of the reference: the same transaction with the GAS
model scaled. If the PoolManager frame list changes with the scale, the divergence comes from contracts that branch on
GAS, not from the PoolManager. usage: python3 gassens.py <cid> <url> <tx> <out.json>"""
import sys, json, replay17 as RP, pyevm_tx17 as P
cid, url, h, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
nets = {n['chainId']: n for n in json.load(open(RP.os.path.join(RP.NR, 'state', 'networks.json')))['networks']}
orig = P.World.__init__; res = {}
for scale in (0.25, 0.5, 1.0, 2.0, 4.0, None):
    def init(self, *a, _s=scale, **k):
        orig(self, *a, **k); self._scale = _s
    P.World.__init__ = init
    real_one = RP.one
    # scale the 'gas' entry the replay puts in ctx
    class Ctx(dict):
        pass
    def patched(cid_, url_, pm_, h_, _s=scale):
        o = RP.P.World.__init__
        def init2(self, *a, **k):
            o(self, *a, **k)
            st = self.__dict__
            class C(dict):
                def __setitem__(s, key, v): dict.__setitem__(s, key, v)
            self.__class__ = type('W', (P.World,), {'__setattr__': lambda s, n, v: object.__setattr__(s, n, ({**v, 'gas': (int(v['gas'] * _s) if _s else None)} if n == 'ctx' and isinstance(v, dict) and 'gas' in v else v))})
        RP.P.World.__init__ = init2
        try: return real_one(cid_, url_, pm_, h_)
        finally: RP.P.World.__init__ = o
    r = patched(cid, url, nets[cid]['poolManager'], h)
    res[str(scale)] = {k: r.get(k) for k in ('pmFramesEqual', 'pmFramesChain', 'logsEqual', 'pmSlotMismatch', 'oracleCallsUsed', 'oracleCallsLeft', 'unsupported')}
    res[str(scale)]['pmRef'] = [f[0] for f in r.get('pmRef', [])]
    print(scale, {k: (v if k != 'pmSlotMismatch' else len(v or [])) for k, v in res[str(scale)].items() if k != 'pmRef'}, flush=True)
    P.World.__init__ = orig
json.dump(res, open(out, 'w'), indent=1)
