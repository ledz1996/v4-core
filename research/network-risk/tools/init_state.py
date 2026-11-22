"""One-time bootstrap: build state/ from the first on-chain probe. Safe to re-run; it never overwrites existing state."""
import json, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
probe = json.load(open(sys.argv[1]))
UNITS = {
    "ethereum-reference": {"title": "Ethereum mainnet reference and cross-chain deployment parity", "chainIds": [1]},
    "op-stack-eth": {"title": "OP Stack chains with ETH gas", "chainIds": [10, 8453, 130, 7777777, 480, 57073, 1868]},
    "op-stack-custom-gas": {"title": "OP Stack chains with a non-ETH gas token", "chainIds": [42220, 196]},
    "arbitrum-family": {"title": "Arbitrum Nitro and Orbit chains", "chainIds": [42161, 4663, 99901]},
    "established-l1": {"title": "Established alternative L1s", "chainIds": [137, 56, 43114]},
    "high-throughput": {"title": "High-throughput chains with modified gas models", "chainIds": [143, 4326]},
    "stablecoin-l1": {"title": "Stablecoin-native L1s", "chainIds": [4217, 5042]},
    "hyperevm": {"title": "HyperEVM", "chainIds": [999]},
}
LENSES = {
    "L1": "Opcodes and EVM semantics: supported fork, opcode behaviour and pricing differences, code size, call gas forwarding, SELFDESTRUCT, EIP-7702, non-EVM execution (WASM, precompile-only accounts)",
    "L2": "State model: transient storage lifetime, transaction boundaries and batching, state changes made outside normal EVM execution (system transactions, fee debits, deposits), account model, address aliasing",
    "L3": "Gas, native currency and token contracts: gas token identity and decimals, ERC-20 aliases of the native asset, enshrined or precompile tokens, issuer controls (freeze, blocklist, seize), fee payment in tokens, block and transaction gas caps",
    "L4": "System contracts, precompiles and predeploys that can move balances, change code, or read privileged state",
    "L5": "Deployment parity and governance: deployed bytecode versus this repo, constructor arguments, owner and protocol fee controller, cross-chain ownership path",
    "L6": "Block production, ordering, finality and upgrade roadmap: sequencer or validator powers, reorg depth, scheduled forks that change any of the above",
}
by_id = {p["chainId"]: p for p in probe["probe"]}
contracts = {n["chainId"]: n["contracts"] for n in probe["networks"]}
nets = []
for uid, u in UNITS.items():
    for cid in u["chainIds"]:
        p = dict(by_id[cid]); p["unit"] = uid; p["contracts"] = contracts[cid]; p.pop("errors", None); p.pop("rpcTried", None)
        nets.append(p)
os.makedirs(f"{R}/state", exist_ok=True)
def write_new(name, obj):
    path = f"{R}/state/{name}"
    if os.path.exists(path): print("keep", name); return
    json.dump(obj, open(path, "w"), indent=1); print("wrote", name)
write_new("networks.json", {"source": "https://docs.uniswap.org/contracts/v4/deployments", "networks": nets})
write_new("ledger.json", {"schema": 1, "cycle": 0, "units": UNITS, "lenses": LENSES,
    "cells": {f"{n['chainId']}:{l}": {"depth": 0, "lastCycle": 0} for n in nets for l in LENSES},
    "leads": [], "history": []})
write_new("findings.json", {"findings": []})
write_new("cleared.json", {"cleared": []})
