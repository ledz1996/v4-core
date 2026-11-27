#!/bin/sh
# eth_call with a state override: code 0x600160020160005260206000f3 (1+2, return 32 bytes) at an empty address
u=$1
curl -s -m 20 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"from":"0x00000000000000000000000000000000000000aa","to":"0x00000000000000000000000000000000000c0de1","data":"0x"},"latest",{"0x00000000000000000000000000000000000c0de1":{"code":"0x600160020160005260206000f3"}}]}' $u | head -c 200
