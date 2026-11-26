#!/bin/bash
# disassemble every dumped function with GNU objdump at its real address
idx=$1; dir=$2; arch=$3
while read name entry end size loc; do
  f=$dir/$(echo "$name" | sed 's/[^A-Za-z0-9_.]/_/g').bin
  echo "### $name $loc"
  objdump -D -b binary -m $arch --adjust-vma=0x$entry $f | sed -n '8,$p'
done < $idx
