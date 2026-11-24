import json
from common import *
import gzip
h = '0x521ce7e7ce7800ab260567eebdbac6c0c965c1c39ec16ca394ce22dd7849f7ce'
for u in TRACE[143]:
    try:
        t = rpc([u], 'debug_traceTransaction', [h, {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}], tries=2)
        print(u, 'call ok', len(json.dumps(t)))
        p = rpc([u], 'debug_traceTransaction', [h, {'tracer': 'prestateTracer'}], tries=2)
        print(u, 'prestate ok', list(p.keys())[:5])
        p = rpc([u], 'debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}], tries=2)
        print(u, 'diff ok', list(p.keys()))
    except Exception as e: print(u, 'err', str(e)[:200])
