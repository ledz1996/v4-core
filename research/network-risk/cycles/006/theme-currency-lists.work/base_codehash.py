# EXTCODEHASH of every Base pool currency through a stub placed by state override (eth_call). Resumable.
# Writes raw/base_codehash.npy (N x 32 bytes, aligned with raw/base_tokens.npy; all 0xff = not read).
import numpy as np, sys, os, time, threading
from concurrent.futures import ThreadPoolExecutor
from common import *
T = np.load('raw/base_tokens.npy'); N = len(T); PER = 4000
FN = 'raw/base_codehash.npy'
H = np.load(FN) if os.path.exists(FN) else np.full((N, 32), 255, dtype=np.uint8)
todo = [i for i in range(0, N, PER) if H[i].min() == 255 and H[i].max() == 255]
print('chunks todo', len(todo), 'of', (N + PER - 1) // PER, flush=True)
US = ['https://mainnet.base.org/', 'https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://base-mainnet.public.blastapi.io', 'https://base.gateway.tenderly.co']
lock = threading.Lock(); done = [0]
def job(i):
    data = '0x' + T[i:i + PER].tobytes().hex() if False else '0x' + ''.join('0' * 24 + bytes(x).hex() for x in T[i:i + PER])
    n = min(PER, N - i)
    for k in range(10):
        u = US[(i // PER + k) % len(US)]
        try:
            r = call_override(u, STUB, data, {STUB: {'code': CODEHASH_STUB}}, timeout=60)
            if len(r) != 2 + 64 * n: raise Exception('short')
            b = np.frombuffer(bytes.fromhex(r[2:]), dtype=np.uint8).reshape(n, 32)
            with lock:
                H[i:i + n] = b; done[0] += 1
                if done[0] % 300 == 0: np.save(FN, H); print('done', done[0], len(todo), time.strftime('%H:%M:%S'), flush=True)
            return
        except Exception as e:
            time.sleep(0.5 + k)
    print('fail', i, flush=True)
with ThreadPoolExecutor(8) as ex: list(ex.map(job, todo))
np.save(FN, H); print('finished', done[0], flush=True)
