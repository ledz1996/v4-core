import sys; sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/039/theme-ethereum-binaries-storage-journal.work/scripts')
import gethj as G
g = G.Geth().new()
print('sdb', hex(g.sdb), 'calls', g.calls, 'stubbed', g.stubbed)
PM = 0x000000000004444c5dc75cB358380D2e3dE08A90
g.tst(PM, 5, 7); print('tld', g.tld(PM, 5), g.tld(PM, 6), g.jlen())
r = g.snap(); g.tst(PM, 5, 9); print(g.tld(PM, 5), g.jlen()); g.revert(r); print(g.tld(PM, 5), g.jlen())
try:
    print(g.sld(PM, 3))
except Exception as e: print('ERR', e)
g = G.Geth().new(); g.db[(PM,3)] = 77
print(g.sld(PM,3), g.orig(PM,3)); g.sst(PM,3,5); print(g.sld(PM,3), g.orig(PM,3), g.jlen())
r=g.snap(); g.sst(PM,3,77); print(g.sld(PM,3), g.orig(PM,3), g.jlen()); g.sst(PM,3,8); g.revert(r); print(g.sld(PM,3), g.orig(PM,3), g.jlen(), g.dbreads)
