"""Cycle 33 ethereum-reference. Runs tools/opdiff/pmdiff.py or pmdiff2.py with Ethereum (publicnode, chain id 1) as the
reference and extra Ethereum endpoints entered under made-up ids 9000xx, so their script results are compared with the
reference build. Read-only (eth_call with state overrides).
Usage: python3 pmalt.py pmdiff|pmdiff2 <out.json> <n scripts> <url> [<url> ...]"""
import sys, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
which, out, n, urls = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
base = [x for x in evm.networks() if x[0] == 1]
extra = [(900000 + i, u.split('/')[2][:16], u) for i, u in enumerate(urls)]
evm.networks = lambda *a, **k: base + extra
sys.argv = [which + '.py', out, n]
runpy.run_path('/home/user/v4-core/research/network-risk/tools/opdiff/' + which + '.py', run_name='__main__')
