#!/bin/bash
# usage: get.sh owner/repo ref path  -> saves under dl/owner_repo@ref/path, logs to dl/fetchlog.txt
r=$1; ref=$2; p=$3
d="dl/${r/\//_}@${ref//\//_}/$p"
mkdir -p "$(dirname "$d")"
if [ -s "$d" ]; then echo "$d"; exit 0; fi
code=$(curl -s -m 60 -o "$d" -w '%{http_code}' "https://raw.githubusercontent.com/$r/$ref/$p")
echo "$(date -u +%FT%TZ) $code https://raw.githubusercontent.com/$r/$ref/$p $(stat -c %s "$d" 2>/dev/null)" >> dl/fetchlog.txt
if [ "$code" != 200 ]; then rm -f "$d"; echo "MISS $code $r $ref $p" >&2; exit 1; fi
echo "$d"
