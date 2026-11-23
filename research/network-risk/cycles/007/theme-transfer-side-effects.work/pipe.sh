#!/bin/sh
# getters (if missing) -> factories -> pairs -> surcharge sweep, one network after the other
for c in "$@"; do
  [ -f raw/getters_$c.json.gz ] || python3 getters.py $c
  python3 facs.py $c
  python3 pairs.py $c
  python3 surcharge.py $c
done
