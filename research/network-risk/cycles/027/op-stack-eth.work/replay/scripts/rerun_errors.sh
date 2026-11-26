#!/bin/sh
# drop error records of one lazy output set so that gdrive.py runs those transactions again. usage: rerun_errors.sh <dir> <glob>
for f in $1/$2; do python3 -c "
import json,sys
f=sys.argv[1]; L=[l for l in open(f) if 'error' not in json.loads(l)]
open(f,'w').writelines(L)" $f; done
