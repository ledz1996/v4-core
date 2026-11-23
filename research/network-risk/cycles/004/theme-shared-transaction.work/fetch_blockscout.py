# Fetch verified source from a Blockscout style explorer into the scratch download directory.
import sys, os, json, requests
from lib import DL
def fetch(base, tag, addr):
    r=requests.get(base+'/api/v2/smart-contracts/'+addr,timeout=60,headers={'user-agent':'curl/8'})
    if r.status_code!=200: return None
    j=r.json()
    if not j.get('source_code'): return {'verified':False,'name':j.get('name'),'proxy':j.get('proxy_type'),'impls':j.get('implementations')}
    d=os.path.join(DL,'%s_%s'%(tag,addr.lower())); os.makedirs(d,exist_ok=True)
    files=[(j.get('file_path') or 'Main.sol',j['source_code'])]+[(x['file_path'],x['source_code']) for x in (j.get('additional_sources') or [])]
    for p,s in files: open(os.path.join(d,p.replace('/','__').replace('..','_')),'w').write(s)
    return {'verified':True,'dir':d,'name':j.get('name'),'files':len(files),'compiler':j.get('compiler_version'),'runs':j.get('optimization_runs'),'full':j.get('is_fully_verified'),'partial':j.get('is_partially_verified'),'proxy':j.get('proxy_type'),'impls':j.get('implementations')}
if __name__=='__main__':
    print(fetch(sys.argv[1],sys.argv[2],sys.argv[3]))
