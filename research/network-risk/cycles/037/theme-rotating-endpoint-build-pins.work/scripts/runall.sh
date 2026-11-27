#!/bin/sh
# cycle 37: pinned runs, one endpoint per line, sets run one after another per endpoint
cd /home/user/v4-core/research/network-risk/cycles/037/theme-rotating-endpoint-build-pins.work
S=scripts/pinrun.py
(for s in ops provevec pmdiff pmdiff2; do python3 -I $S https://polygon-bor-rpc.publicnode.com $s out/pin-polygon-$s.json --builds "bor/a863b8e5cce1/v2.11.1-private/linux-amd64/go1.26.10,bor/280514fa9fb7/v2.11.1-private/linux-amd64/go1.26.10,bor/ebcfea01452d/v2.11.1-private/linux-amd64/go1.26.10,bor/cb3d19c5f690/v2.11.1-private/linux-amd64/go1.26.10,bor/f2a2d63e69f6/v2.11.1-private/linux-amd64/go1.26.10" --threads 3 > out/pin-polygon-$s.log 2>&1; done) &
(for s in ops provevec pmdiff pmdiff2; do python3 -I $S https://forno.celo.org $s out/pin-celo-$s.json --builds "reth/v2.2.0-74cc8bb/x86_64-unknown-linux-gnu,Geth/v0.1.0-untagged-c7ed55b8-20260817/linux-amd64/go1.24.13" --threads 3 > out/pin-celo-$s.log 2>&1; done) &
(for s in ops provevec pmdiff pmdiff2; do python3 -I $S https://bsc-dataseed1.bnbchain.org $s out/pin-bscds1-$s.json --builds "Geth/v1.8.2/linux-amd64/go1.26.10,Geth/v1.8.2-4e1c8247-20261104/linux-amd64/go1.26.10" --threads 2 > out/pin-bscds1-$s.log 2>&1; done) &
wait
