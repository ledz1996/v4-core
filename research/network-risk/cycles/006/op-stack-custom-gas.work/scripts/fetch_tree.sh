#!/bin/bash
# usage: fetch_tree.sh <owner/repo> <ref> <outdir> <path>...
repo=$1; ref=$2; out=$3; shift 3
for p in "$@"; do
  mkdir -p "$out/$(dirname "$p")"
  code=$(curl -s -m 40 -L -o "$out/$p" -w '%{http_code}' "https://raw.githubusercontent.com/$repo/$ref/$p")
  if [ "$code" != 200 ]; then rm -f "$out/$p"; fi
  echo "$code $p $( [ -f "$out/$p" ] && wc -l < "$out/$p")"
done
