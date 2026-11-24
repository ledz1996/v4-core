import sys, rerun as R, pyevm2
DB = []
orig = pyevm2.World.__init__
def init(self, *a, **k): orig(self, *a, **k); DB.append(self)
pyevm2.World.__init__ = init
cid, h = int(sys.argv[1]), sys.argv[2]
R.rerun(cid, h)
w = DB[0]
ENV = {0x31: 'BALANCE', 0x32: 'ORIGIN', 0x3a: 'GASPRICE', 0x40: 'BLOCKHASH', 0x41: 'COINBASE', 0x42: 'TIMESTAMP', 0x43: 'NUMBER', 0x44: 'PREVRANDAO', 0x45: 'GASLIMIT', 0x46: 'CHAINID', 0x47: 'SELFBALANCE', 0x48: 'BASEFEE', 0x5a: 'GAS', 0x3b: 'EXTCODESIZE', 0x3f: 'EXTCODEHASH'}
for a in sys.argv[3:]:
    a = int(a, 16); code = w.codes[a]; got = {}
    for pc in w.cover.get(a, ()):
        op = code[pc]
        if op in ENV: got[ENV[op]] = got.get(ENV[op], 0) + 1
    print(hex(a), got)
print('env', {k: v for k, v in w.env.items() if k != 'blockhash'})
