#!/bin/bash
# usage: show.sh FILE FROM TO  -- prints a line range of extracted audit text with blank and boilerplate lines removed
awk -v a="$2" -v b="$3" 'NR>=a && NR<=b' "$1" | tr -d '\357\202\247\246\250\251' | grep -v '^[[:space:]]*$' \
 | grep -v -E 'bytes16\), you cannot make|the type. \(https://docs.soliditylang|variables-functions-and-libraries|mended in the documentation|it in a context where this is important|Recommendation Properly clean extra bits|as +it +they +were +256|variables of a type that spans less|Description +Here +local +variables' | cut -c1-200
