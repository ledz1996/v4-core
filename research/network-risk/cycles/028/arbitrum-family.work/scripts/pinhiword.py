"""Cycle 28 arbitrum-family: run cycle 27's hiword.py vectors through pinrun.py's build-bracketed loop,
so each batch is attributed to one backend (Robinhood Chain mixes amd64 and arm64 per request).
Read-only eth_call with a state override. Usage: python3 pinhiword.py <out.json> <url> <build substring>"""
import sys
R = '/home/user/v4-core/research/network-risk'
sys.path.insert(0, R + '/tools/opdiff'); sys.path.insert(0, R + '/cycles/027/ethereum-reference.work'); sys.path.insert(0, R + '/cycles/027/op-stack-eth.work/scripts')
import pinrun, hiword
pinrun.extra = lambda seed=0: hiword.vectors()
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3], 'extra', '300', '120']
pinrun.main()
