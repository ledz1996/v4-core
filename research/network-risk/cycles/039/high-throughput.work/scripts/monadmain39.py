"""Cycle 39: refetch Monad main files under category/vm listed by cycle 37 and compare byte for byte with the cycle 37
copy. Read-only fetches from raw.githubusercontent.com. usage: python3 -I monadmain39.py"""
import subprocess, os, filecmp, json
C = '/home/user/v4-core/research/network-risk/cycles/037/high-throughput.work'
W = '/home/user/v4-core/research/network-risk/cycles/039/high-throughput.work'
D = W + '/dl/monadmain'; os.makedirs(D, exist_ok=True)
prev = json.load(open(C + '/out/monadmain37.json'))
res = {'same': [], 'diff': [], 'miss': []}
for s in prev['same'] + prev['diff']:
    b = s.replace('/', '_')
    r = subprocess.run(['curl', '-s', '-m', '30', '-o', f'{D}/{b}', '-w', '%{http_code}', 'https://raw.githubusercontent.com/category-labs/monad/main/' + s], capture_output=True, text=True)
    if r.stdout != '200': res['miss'].append(s); continue
    (res['same'] if filecmp.cmp(f'{C}/dl/monadmain/{b}', f'{D}/{b}', shallow=False) else res['diff']).append(s)
json.dump(res, open(W + '/out/monadmain39.json', 'w'), indent=1)
print(len(res['same']), res['diff'], res['miss'])
