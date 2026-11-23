# debug_traceCall helper (callTracer): print the call tree of a simulated call. Read-only.
import json
from lib import *
from sigs import lookup
_names = {}
def name(selhex):
    if selhex not in _names:
        _names.update(lookup([selhex])); _names.setdefault(selhex, '')
    return _names[selhex] or selhex
def show(c, depth=0, maxdepth=6, out=None):
    out = out if out is not None else []
    inp = c.get('input', '0x'); s = inp[2:10]
    out.append('%s%s %s -> %s %s val=%s in=%s%s%s' % ('  ' * depth, c.get('type'), c.get('from', '')[:10], c.get('to', '')[:12], name(s).split('(')[0] if s else '(empty)', int(c.get('value', '0x0'), 16) if c.get('value') else 0, inp[10:10 + 64 * 4], ' ERR=' + str(c.get('error')) if c.get('error') else '', ' out=' + c.get('output', '')[:138] if c.get('output') else ''))
    if depth < maxdepth:
        for x in c.get('calls', []) or []: show(x, depth + 1, maxdepth, out)
    return out
def trace(u, tx, block='latest', tracer='callTracer', cfg=None, overrides=None):
    opt = {'tracer': tracer}
    if cfg: opt['tracerConfig'] = cfg
    if overrides: opt['stateOverrides'] = overrides
    j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceCall', 'params': [tx, block, opt]}, timeout=60)
    if 'error' in j: raise Exception(json.dumps(j['error'])[:300])
    return j['result']
