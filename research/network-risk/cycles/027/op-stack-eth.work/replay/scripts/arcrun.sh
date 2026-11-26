#!/bin/sh
# L-1014 rerun of the 37 set-aside Arc transactions, bracketed by web3_clientVersion
U=https://rpc.mainnet.arc.io
cd "$(dirname "$0")"
python3 -c "from rpcu import call;import json,time;print(json.dumps({'tag':'start','client':call('$U','web3_clientVersion',[]),'t':time.time()}))" >> ../raw/5042/brackets.jsonl
python3 drive24.py $U 0 37 ../raw/5042/setaside_pass1.jsonl > ../raw/5042/setaside_pass1.log 2>&1
python3 -c "from rpcu import call;import json,time;print(json.dumps({'tag':'end','client':call('$U','web3_clientVersion',[]),'t':time.time()}))" >> ../raw/5042/brackets.jsonl
