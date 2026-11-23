# Base: EXTCODESIZE for every currency whose code hash is unique among pool currencies (2.56 million), to group them by code size.
# Then build the test set: every token of a code hash family with 2 to 1,000 members, 30 tokens of each larger family,
# every token of a code size group with at most 20 members and 20 tokens of each larger size group. Writes raw/base_testset.json.gz.
import numpy as np, json, gzip, os, time, threading, random, collections
from concurrent.futures import ThreadPoolExecutor
from common import *
SIZE_STUB = CODEHASH_STUB.replace('8035' + '3f', '8035' + '3b')
T = np.load('raw/base_tokens.npy'); inv = np.load('raw/base_family_index.npy'); fs = np.load('raw/base_family_sizes.npy')
single = np.nonzero(fs[inv] == 1)[0]; print('singletons', len(single), flush=True)
FN = 'raw/base_single_sizes.npy'; PER = 4000
Sz = np.load(FN) if os.path.exists(FN) else np.full(len(single), -1, dtype=np.int32)
US = ['https://mainnet.base.org/', 'https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://base-mainnet.public.blastapi.io', 'https://base.gateway.tenderly.co']
lock = threading.Lock(); done = [0]
todo = [i for i in range(0, len(single), PER) if Sz[i] == -1]
def job(i):
    idx = single[i:i + PER]; data = '0x' + ''.join('0' * 24 + bytes(T[j]).hex() for j in idx)
    for k in range(10):
        try:
            r = call_override(US[(i // PER + k) % len(US)], STUB, data, {STUB: {'code': SIZE_STUB}}, timeout=60)
            if len(r) != 2 + 64 * len(idx): raise Exception('short')
            v = [int(r[2 + 64 * m + 48: 66 + 64 * m], 16) for m in range(len(idx))]
            with lock: Sz[i:i + len(idx)] = v; done[0] += 1
            return
        except Exception as e: time.sleep(0.5 + k)
    print('fail', i, flush=True)
with ThreadPoolExecutor(8) as ex: list(ex.map(job, todo))
np.save(FN, Sz); print('sizes read', (Sz >= 0).sum(), 'distinct sizes', len(np.unique(Sz)), 'no code', (Sz == 0).sum(), flush=True)
random.seed(6); test = {}
groups = collections.defaultdict(list)
for j in np.nonzero(fs[inv] > 1)[0]: groups[int(inv[j])].append(int(j))
nfam = 0
for g, mem in groups.items():
    nfam += 1; pick = mem if len(mem) <= 1000 else random.sample(mem, 30)
    for j in pick: test[j] = 'hash'
sg = collections.defaultdict(list)
for k, j in enumerate(single): sg[int(Sz[k])].append(int(j))
for s, mem in sg.items():
    pick = mem if len(mem) <= 20 else random.sample(mem, 20)
    for j in pick: test.setdefault(j, 'size')
toks = ['0x' + bytes(T[j]).hex() for j in sorted(test)]
json.dump(dict(tokens=toks, families=nfam, sizeGroups=len(sg), bigSizeGroups=sorted(((len(m), s) for s, m in sg.items()), reverse=True)[:40]), gzip.open('raw/base_testset.json.gz', 'wt'))
print('test set', len(toks), 'hash families', nfam, 'size groups', len(sg), 'largest size groups', sorted(((len(m), s) for s, m in sg.items()), reverse=True)[:12], flush=True)
