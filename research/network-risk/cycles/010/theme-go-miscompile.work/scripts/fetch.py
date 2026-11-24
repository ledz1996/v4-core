import subprocess,os,sys
base='/home/user/v4-core/research/network-risk/cycles/010/theme-go-miscompile.work/dl'
files="core/vm/instructions.go core/vm/interpreter.go core/vm/stack.go core/vm/memory.go core/vm/common.go core/vm/analysis_legacy.go core/vm/analysis.go core/vm/eips.go core/vm/jump_table.go core/vm/evm.go core/vm/contract.go core/vm/operations_acl.go core/vm/gas_table.go core/vm/memory_table.go core/state/transient_storage.go core/state/journal.go core/state/statedb.go core/state/state_object.go core/state/access_list.go core/vm/instructions.libevm.go core/vm/interpreter.libevm.go core/vm/evm.libevm.go go.mod".split()
for repo,ref,d in [('OffchainLabs/go-ethereum','0e44603','nitro'),('bnb-chain/bsc','v1.8.2','bsc'),('0xPolygon/bor','v2.11.1','bor'),('ava-labs/libevm','d398bc4dbe41','libevm')]:
    os.makedirs(f'{base}/{d}',exist_ok=True); ok=[]
    for f in files:
        url=f'https://raw.githubusercontent.com/{repo}/{ref}/{f}'
        r=subprocess.run(['curl','-sL','-w','%{http_code}',url],capture_output=True)
        code=r.stdout[-3:]; body=r.stdout[:-3]
        if code==b'200':
            open(f'{base}/{d}/'+f.replace('/','_'),'wb').write(body); ok.append(f)
    print(d,len(ok),ok)
