"""Failed transactions on Monad and the status that block execution stored for each call frame.
In v0.16.7 the interpreter ends an out-of-gas frame with OutOfGas (interpreter/stack.hpp:44), while
compiled code jumps to error_label_, which exits with StatusCode::Error (compiler/ir/x86/emitter.cpp:636,679,
1054-1069, 1273-1354); debug.rs maps status 3 to "out of gas" and any other failure to "error".
So a frame on a given code that runs out of gas shows "out of gas" when it was interpreted and
"error" when it ran compiled (unless the gas ran out in a runtime helper).
Usage: python3 oogscan.py <hi> <nblocks> <out.json>"""
import sys, json, time, collections, threading, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
URLS = ['https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
def call(method, params, k=0):
    for a in range(10):
        try: return rpc(URLS[(k + a) % len(URLS)], method, params, timeout=60)
        except Exception as e:
            last = e; time.sleep(0.5 * (a + 1))
    raise last
def walk(f, depth=0):
    yield f, depth
    for c in f.get('calls') or []: yield from walk(c, depth + 1)
def job(b):
    try: rs = call('eth_getBlockReceipts', [hex(b)], b)
    except Exception as e: return b, None, str(e)[:100]
    out = []
    for t in rs:
        if t['status'] != '0x0': continue
        try: tr = call('debug_traceTransaction', [t['transactionHash'], {'tracer': 'callTracer'}], b)
        except Exception as e: out.append({'tx': t['transactionHash'], 'err': str(e)[:100]}); continue
        fr = []
        for f, d in walk(tr):
            if f.get('error'):
                fr.append({'to': (f.get('to') or '').lower(), 'type': f.get('type'), 'error': f['error'], 'gas': int(f['gas'], 16), 'gasUsed': int(f['gasUsed'], 16), 'depth': d, 'sel': (f.get('input') or '')[:10]})
        out.append({'tx': t['transactionHash'], 'block': b, 'frames': fr})
    return b, out, None
if __name__ == '__main__':
    hi, n, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    res = {'blocks': [hi - n + 1, hi], 'blockErrors': 0, 'failedTx': 0, 'traceErrors': 0, 'frameErrors': collections.Counter(), 'pmFrames': [], 'oogLike': []}
    with cf.ThreadPoolExecutor(4) as ex:
        for i, (b, out, err) in enumerate(ex.map(job, range(hi - n + 1, hi + 1))):
            if out is None: res['blockErrors'] += 1; continue
            for t in out:
                res['failedTx'] += 1
                if 'err' in t: res['traceErrors'] += 1; continue
                for f in t['frames']:
                    res['frameErrors'][f['error']] += 1
                    rec = {**f, 'tx': t['tx'], 'block': b}
                    if f['to'] == PM: res['pmFrames'].append(rec)
                    if f['error'] in ('out of gas', 'error') and len(res['oogLike']) < 3000: res['oogLike'].append(rec)
            if i % 500 == 0:
                print(i, res['failedTx'], dict(res['frameErrors']), len(res['pmFrames']), flush=True)
                json.dump(res, open(outp, 'w'), indent=1)
    json.dump(res, open(outp, 'w'), indent=1); print('done', res['failedTx'], dict(res['frameErrors']), len(res['pmFrames']))
