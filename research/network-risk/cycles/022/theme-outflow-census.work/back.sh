#!/bin/bash
# Runs census3 over contiguous pieces going back from a block, newest piece first. Read-only.
# usage: back.sh <cid> <url> <chunk> <seg> <workers> <top> <bottom> <piece>
cd "$(dirname "$0")"
cid=$1; url=$2; chunk=$3; seg=$4; w=$5; top=$6; bottom=$7; piece=$8
b2=$top
while [ $b2 -ge $bottom ]; do b1=$((b2-piece+1)); [ $b1 -lt $bottom ] && b1=$bottom
  python3 census3.py $cid $b1 $b2 $seg back$b1 $url $chunk $w > raw/census3_${cid}_back$b1.log 2>&1; b2=$((b1-1)); done
