# Distinct pool currencies of Base from raw/base_init.bin, with pool counts and first block. Writes raw/base_tokens.npy (N x 20 bytes),
# raw/base_token_pools.npy (pool count per token) and raw/base_summary.json.
import numpy as np, struct, json, collections
bodies = []; wins = 0; lo = 1 << 62; hi = 0
with open('raw/base_init.bin', 'rb') as f:
    while True:
        h = f.read(8)
        if len(h) < 8: break
        a, n = struct.unpack('>II', h); wins += 1; lo = min(lo, a); hi = max(hi, a + 999)
        if n: bodies.append(f.read(102 * n))
A = np.frombuffer(b''.join(bodies), dtype=np.uint8).reshape(-1, 102); del bodies
ids = np.ascontiguousarray(A[:, 4:36]).view('V32').ravel()
uid = np.unique(ids); print('rows', len(A), 'distinct pool ids', len(uid), 'windows', wins, lo, hi, flush=True)
c = np.concatenate([np.ascontiguousarray(A[:, 36:56]), np.ascontiguousarray(A[:, 56:76])]).view('V20').ravel()
u, cnt = np.unique(c, return_counts=True)
np.save('raw/base_tokens.npy', u.view(np.uint8).reshape(-1, 20)); np.save('raw/base_token_pools.npy', cnt)
hooks = np.ascontiguousarray(A[:, 76:96]).view('V20').ravel(); hu, hc = np.unique(hooks, return_counts=True)
top = sorted(zip(hc.tolist(), [bytes(x).hex() for x in hu.view(np.uint8).reshape(-1, 20)]), reverse=True)[:15]
topc = sorted(zip(cnt.tolist(), [bytes(x).hex() for x in u.view(np.uint8).reshape(-1, 20)]), reverse=True)[:15]
json.dump(dict(pools=int(len(A)), distinctPoolIds=int(len(uid)), windows=wins, lo=lo, hi=hi, currencies=int(len(u)), hooks=int(len(hu)), topHooks=top, topCurrencies=topc,
               tokensInOnePool=int((cnt == 1).sum())), open('raw/base_summary.json', 'w'), indent=1)
print(open('raw/base_summary.json').read())
