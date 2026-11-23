# Base part two: balances of the test set (raw/base_testset.json.gz), then the universe file for the sweep scripts.
import json, gzip
import balances
toks = json.load(gzip.open('raw/base_testset.json.gz'))['tokens']
balances.run(8453, 500, 6, toks=[t for t in toks if int(t, 16) != 0]); balances.universe_file(8453)
