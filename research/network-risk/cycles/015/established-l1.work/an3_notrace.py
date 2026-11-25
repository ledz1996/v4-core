import sys, runpy
D='/home/user/v4-core/research/network-risk/cycles/012/theme-mined-liquidity-2.work'
sys.path.insert(0, D)
import lib
lib.LOG_URLS[56] = ['https://rpc-bsc.48.club']
for k in list(lib.TRACE_URLS): lib.TRACE_URLS[k] = ['https://bsc-rpc.publicnode.com'] if k == 56 else lib.TRACE_URLS[k]
sys.argv = [D + '/analyze3.py'] + sys.argv[1:]
runpy.run_path(D + '/analyze3.py', run_name='__main__')
