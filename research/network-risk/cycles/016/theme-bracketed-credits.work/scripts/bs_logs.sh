#!/bin/bash
# usage: bs_logs.sh <apibase> <address> <topic0> <topic1>
curl -s -m 60 "$1?module=logs&action=getLogs&fromBlock=0&toBlock=latest&address=$2&topic0=$3&topic1=$4&topic0_1_opr=and"
