#!/bin/bash
# usage: rpc.sh <url> <method> <params-json>
curl -s --max-time 40 -X POST -H 'content-type: application/json' --data "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$2\",\"params\":$3}" "$1"
