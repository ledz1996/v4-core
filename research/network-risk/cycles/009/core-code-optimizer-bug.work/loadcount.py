"""Count mload, sload and keccak256 per Yul function in two IR texts (before and after one LoadResolver step)."""
import re, sys, json
def strip(t):
    t = re.sub(r'/\*\*.*?\*/', '', t, flags=re.S); t = re.sub(r'///[^\n]*', '', t); return t
def funcs(t):
    # split runtime object into functions by brace matching
    out = {}; 
    for m in re.finditer(r'function (\w+)\s*\(', t):
        i = t.index('{', m.end()); d = 0; j = i
        while True:
            c = t[j]
            if c == '{': d += 1
            elif c == '}':
                d -= 1
                if d == 0: break
            j += 1
        out[m.group(1)] = t[i:j + 1]
    return out
def obj(t, name):
    i = t.index(f'object "{name}"'); return t[i:]
if __name__ == '__main__':
  a = strip(open(sys.argv[1]).read()); b = strip(open(sys.argv[2]).read())
  res = {}
  for label, (x, y) in {'creation': (a[:a.index('object "PoolManager_1216_deployed"')], b[:b.index('object "PoolManager_1216_deployed"')]),
                        'runtime': (obj(a, 'PoolManager_1216_deployed'), obj(b, 'PoolManager_1216_deployed'))}.items():
      fa, fb = funcs(x), funcs(y)
      # body outside functions
      tot = {}
      for op in ['mload', 'sload', 'keccak256', 'tload', 'mstore', 'sstore', 'tstore']:
          ca, cb = len(re.findall(r'\b' + op + r'\(', x)), len(re.findall(r'\b' + op + r'\(', y)); tot[op] = (ca, cb)
      per = {}
      for f in sorted(set(fa) | set(fb)):
          d = {}
          for op in ['mload', 'sload', 'keccak256', 'mstore', 'sstore']:
              ca = len(re.findall(r'\b' + op + r'\(', fa.get(f, ''))); cb = len(re.findall(r'\b' + op + r'\(', fb.get(f, '')))
              if ca != cb: d[op] = (ca, cb)
          if d or (f in fa) != (f in fb): per[f] = d if (f in fa and f in fb) else ('only pre' if f in fa else 'only post')
      res[label] = {'totals': tot, 'changed_functions': per}
  json.dump(res, open(sys.argv[3], 'w'), indent=1); print(json.dumps(res, indent=1))
