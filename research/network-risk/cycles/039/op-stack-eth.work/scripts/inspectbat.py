"""Run the battery.py and targeted.py vectors through debug_traceCall with callTracer, which
executes on revm's inspector loop (inspect_tx), the loop an op-reth sequencer in Lagoon produce
mode uses for every transaction. Compares the traced call's output with the reference words.
Usage: python3 -I inspectbat.py <toolsdir> <out.json> <rpc> [max vectors]"""
import sys, json, time
sys.path.insert(0, sys.argv[1])
from evm import rpc, STUB
import battery as B, targeted as T
out, url = sys.argv[2], sys.argv[3]; cap = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
code = B.dispatcher(); V = (B.vectors() + T.vectors())[:cap]
bad = []; done = 0; errors = []; size = 400
cv = rpc(url, 'web3_clientVersion', [])
for i in range(0, len(V), size):
    batch = V[i:i + size]; data = B.encode(batch); r = None
    for k in range(4):
        try:
            r = rpc(url, 'debug_traceCall', [{'to': STUB, 'data': '0x' + data.hex(), 'gas': hex(30_000_000)}, 'latest',
                     {'tracer': 'callTracer', 'stateOverrides': {STUB: {'code': '0x' + code.hex()}}}], timeout=120); break
        except Exception as e:
            err = str(e)[:150]; time.sleep(3 * (k + 1))
    if r is None: errors.append((i, err)); continue
    res = bytes.fromhex(r.get('output', '0x')[2:])
    if len(res) != 32 * len(batch): errors.append((i, 'short %d %s' % (len(res), r.get('error')))); continue
    exp = B.expected(batch, data)
    for k, (t, e) in enumerate(zip(batch, exp)):
        got = int.from_bytes(res[32 * k:32 * k + 32], 'big')
        if got != e: bad.append({'op': t[0], 'a': hex(t[1]), 'b': hex(t[2]), 'c': hex(t[3]), 'got': hex(got), 'want': hex(e)})
    done += len(batch)
json.dump({'rpc': url, 'clientVersion': cv, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:20]}, open(out, 'w'), indent=1)
print(url, cv, 'ran', done, '/', len(V), 'mismatches', len(bad), 'errors', len(errors), errors[:2])
