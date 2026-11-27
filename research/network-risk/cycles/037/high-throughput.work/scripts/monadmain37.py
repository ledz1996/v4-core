"""Cycle 37: refetch the cycle 35 copy of Monad main under category/vm (file names with / written as _) and compare
byte for byte. Read-only fetches from raw.githubusercontent.com. usage: python3 -I monadmain37.py"""
import itertools, subprocess, os, filecmp, json
O = '/home/user/v4-core/research/network-risk/cycles/035/high-throughput.work/dl/monadmain'
W = '/home/user/v4-core/research/network-risk/cycles/037/high-throughput.work'
D = W + '/dl/monadmain'; os.makedirs(D, exist_ok=True)
res = {'same': [], 'diff': [], 'miss': [], 'skipped404': []}
for b in sorted(os.listdir(O)):
    if open(f'{O}/{b}', 'rb').read(14).startswith(b'404: Not Found'): res['skipped404'].append(b); continue
    parts = b.split('_'); n = len(parts) - 1; found = None
    masks = sorted(itertools.product([0, 1], repeat=max(n - 2, 0)), key=lambda m: -sum(m))
    for mask in masks:
        s = parts[0] + '/' + parts[1] + '/' + parts[2]
        for i, m in enumerate(mask): s += ('/' if m else '_') + parts[i + 3]
        r = subprocess.run(['curl', '-s', '-m', '30', '-o', f'{D}/{b}', '-w', '%{http_code}', 'https://raw.githubusercontent.com/category-labs/monad/main/' + s], capture_output=True, text=True)
        if r.stdout == '200': found = s; break
    if not found: res['miss'].append(b)
    elif filecmp.cmp(f'{O}/{b}', f'{D}/{b}', shallow=False): res['same'].append(found)
    else: res['diff'].append(found)
json.dump(res, open(W + '/out/monadmain37.json', 'w'), indent=1)
print(len(res['same']), res['diff'], res['miss'], len(res['skipped404']))
