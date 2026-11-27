#!/bin/bash
# dis.sh <bin> <fde> <outprefix> <hex>... : disassemble whole functions (FDE ranges) to text, reads only
B=$1; F=$2; P=$3; shift 3
for a in "$@"; do r=$(grep -m1 "^0*$a\.\.\." $F); hi=$(echo ${r#*...} | sed 's/^0*//'); objdump -d --no-show-raw-insn -M intel --start-address=0x$a --stop-address=0x$hi $B | tail -n +7 | sed -E 's/<_ZN[^>]*>//;s/^ +//' > $P-$a.s; echo "$a $hi $(wc -l < $P-$a.s)"; done
