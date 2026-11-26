#!/bin/sh
# Polygon: publicnode (private bor builds) all sequences, c2 on the other bor endpoints; Ethereum: repeat c2, c, b and
# a64 on the Pocket gateway so that some calls are bracketed by erigon on both sides (file tag erigon-<i>)
cd "$(dirname "$0")/.."
python3 -I scripts/chainrun.py out 137 https://polygon-bor-rpc.publicnode.com a64 b c c2 d300 e a512 > out/logs/run-137-publicnode.log 2>&1
python3 -I scripts/chainrun.py out 137 https://rpc-mainnet.matic.quiknode.pro c2 > out/logs/c2-137-qn.log 2>&1
python3 -I scripts/chainrun.py out 137 https://poly.api.pocket.network c2 > out/logs/c2-137-pocket.log 2>&1
for i in 1 2 3 4 5 6 7 8; do
  ERIGON_TAG=$i python3 -I scripts/chainrun.py out 1 https://eth.api.pocket.network c2 c b a64 > out/logs/eth-rep-$i.log 2>&1
done
echo RUN2DONE
