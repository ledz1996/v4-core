"""Run the battery and targeted vector sets of tools/opdiff against the HyperEVM testnet endpoint (chain 998),
which receives network upgrades before mainnet. Read-only eth_call with state override."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery, targeted
U = 'https://rpc.hyperliquid-testnet.xyz/evm'
out = {}
V = battery.vectors(); d, bad, err = battery.run(U, battery.dispatcher(), V)
out['battery'] = {'vectors': len(V), 'ran': d, 'mismatches': len(bad), 'examples': bad[:10], 'errors': err[:10]}
print('battery', out['battery']['ran'], len(bad), len(err), flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
