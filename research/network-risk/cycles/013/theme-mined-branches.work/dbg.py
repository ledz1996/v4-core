import sys, json
import rerun as R, pyevm2
orig = pyevm2.World.__init__
def init(self, *a, **k):
    orig(self, *a, **k); self.calllog = []; DB.append(self)
pyevm2.World.__init__ = init; DB = []
r = R.rerun(int(sys.argv[1]), sys.argv[2])
r.pop('branches', None); r.pop('sels', None)
print(json.dumps(r)[:600])
for x in DB[0].calllog[:int(sys.argv[3]) if len(sys.argv) > 3 else 60]: print(x)
