#!/bin/bash
# cycle 39: battery, targeted, pmdiff (250) and pmdiff2 (300) on Ethereum Sepolia (Amsterdam rules) next to the mainnet reference
cd "$(dirname "$0")/.."
export EXTRA='11155111|Sepolia|https://ethereum-sepolia-rpc.publicnode.com'
python3 scripts/withnets.py battery.py out/sepolia/battery.json 11155111 > out/sepolia/battery.log 2>&1
python3 scripts/withnets.py targeted.py out/sepolia/targeted.json 11155111 > out/sepolia/targeted.log 2>&1
python3 scripts/withnets.py pmdiff.py out/sepolia/pmdiff.json 250 11155111 > out/sepolia/pmdiff.log 2>&1
python3 scripts/withnets.py pmdiff2.py out/sepolia/pmdiff2.json 300 11155111 > out/sepolia/pmdiff2.log 2>&1
echo ALLDONE > out/sepolia/ALLDONE
