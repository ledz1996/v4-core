import sys, json
import rerun as R, pyevm2
orig = pyevm2.World.__init__
def init(self, *a, **k):
    orig(self, *a, **k); self.calllog = []; DB.append(self)
pyevm2.World.__init__ = init; DB = []
r = R.rerun(int(sys.argv[1]), sys.argv[2])
cl = DB[0].calllog
print(len(cl), 'calls; failed:')
for x in cl:
    if not x[4]: print(x)
print('last:'); [print(x) for x in cl[-6:]]
