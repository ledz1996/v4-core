#!/bin/sh
# Part two pipeline for one network: the sweep scripts of cycle 5, unchanged, on the tokens of raw/universe_<cid>.json.gz.
c=$1
python3 xfer_sweep.py $c > raw/xfer_$c.log 2>&1
python3 third_sweep.py $c > raw/third_$c.log 2>&1
python3 codehash.py $c > raw/codehash_$c.log 2>&1
python3 tokcode.py $c > raw/tokcode_$c.log 2>&1
python3 proxies.py $c > raw/proxies_$c.log 2>&1
python3 siglookup.py > raw/siglookup_$c.log 2>&1
python3 prices.py $c > raw/prices_$c.log 2>&1
python3 families.py $c > raw/families_$c.log 2>&1
python3 assign_sweep.py $c > raw/assign_$c.log 2>&1
