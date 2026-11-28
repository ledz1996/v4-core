import sys; sys.path.insert(0, '.')
from celoj import Machine, Stop
mc = Machine('celo', 'A', 1)
A = 0x000000000004444c5dc75cb358380d2e3de08a90
mc.put_account(A); mc.backing[(A, 5)] = 77
print('sload', mc.sload(A, 5), 'db', mc.dbcalls, 'jlen', mc.jlen())
print('sload', mc.sload(A, 5), 'db', mc.dbcalls, 'jlen', mc.jlen())
print('sstore', mc.sstore(A, 5, 9), 'jlen', mc.jlen())
print('rec', mc.slot_record(A, 5))
cp = mc.checkpoint(); print('cp', cp, 'depth', mc.depth())
mc.sstore(A, 5, 10); mc.tstore(A, 3, 44); print('tload', mc.tload(A, 3), 'jlen', mc.jlen(), mc.transient_words())
mc.revert(cp); print('after revert rec', mc.slot_record(A, 5), 'tload', mc.tload(A, 3), 'jlen', mc.jlen(), 'depth', mc.depth())
print('steps', mc.cpu.steps)
