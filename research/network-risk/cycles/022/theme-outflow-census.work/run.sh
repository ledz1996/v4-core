#!/bin/bash
# per chain: gapcheck2 (deploy given, EXTRA windows at the census range starts), then census3 ranges. Read-only.
cd "$(dirname "$0")"
cid=$1; pm=$2; dep=$3; url=$4; chunk=$5; seg=$6; workers=$7; shift 7
# remaining args: tag:B1:B2 ...
extra=$(for r in "$@"; do echo "$r" | cut -d: -f2; done | paste -sd,)
DEPLOY=$dep DEPLOYSRC="eth_getCode at deploy-1 and deploy" EXTRA=$extra python3 gapcheck2.py $cid $pm raw/gap-$cid.json ${GAPURLS:-$url} > raw/gap-$cid.log 2>&1
for r in "$@"; do IFS=: read tag b1 b2 <<< "$r"; python3 census3.py $cid $b1 $b2 $seg $tag $url $chunk $workers > raw/census3_${cid}_$tag.log 2>&1; done
