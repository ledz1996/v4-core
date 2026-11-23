#!/bin/bash
# slots then mode B sweep for one network
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
python3 slots.py $1 > raw/slots_$1.log 2>&1 && python3 sweep.py B $1 > raw/sweepB_$1.log 2>&1
