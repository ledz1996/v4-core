# For each candidate with verified source: list state mappings and the lines that move value (burn, take, mint, settle, transfer, value calls).
import sys, re
from common import *
cand = json.load(open(os.path.join(RAW, 'cand.json')))
def src(cid, h):
    for d in (RAW, os.path.join(C5, 'raw')):
        try:
            j = json.load(open(os.path.join(d, 'src', '%d_%s.json' % (cid, h))))
            if 'sources' in j: return j
        except Exception: pass
SKIPDIR = re.compile(r'(^|/)(lib|node_modules|@openzeppelin|@uniswap|v4-core|v4-periphery|solmate|solady|forge-std|openzeppelin-contracts|permit2)/')
def scan(cid, h, full=False):
    j = src(cid, h)
    if not j: return None
    name = (j.get('compilation') or {}).get('name')
    out = ['## %d %s %s  (%s)' % (cid, h, name, j.get('_from', ''))]
    files = [(k, v['content']) for k, v in j['sources'].items() if not SKIPDIR.search(k) or k.split('/')[-1].split('.')[0] == name]
    for k, c in files:
        lines = c.split('\n'); hits = []
        for i, l in enumerate(lines):
            s = l.strip()
            if s.startswith('//') or s.startswith('*') or s.startswith('/*'): continue
            if re.search(r'^\s*mapping\s*\(', l) or re.search(r'\.(burn|take|mint|settle|settleFor|sync|safeTransfer|safeTransferFrom|transfer|transferFrom|safeTransferETH|forceApprove|approve|donate|collect|clear)\s*\(', l) or re.search(r'call\{\s*value', l) or re.search(r'function\s+_?(before|after)(Initialize|Swap|AddLiquidity|RemoveLiquidity|Donate)\b', l) or (full and re.search(r'function\s+\w+\s*\(', l) and re.search(r'external|public', ''.join(lines[i:i + 4])) and not re.search(r'\bview\b|\bpure\b', ''.join(lines[i:i + 4]))):
                hits.append('  %s:%d: %s' % (k.split('/')[-1], i + 1, s[:170]))
        if hits: out.append(' file %s (%d lines)' % (k, len(lines))); out += hits
    return '\n'.join(out)
if __name__ == '__main__':
    if len(sys.argv) > 2:
        print(scan(int(sys.argv[1]), sys.argv[2].lower(), full=True))
    else:
        f = open(os.path.join(RAW, 'srcscan.txt'), 'w'); n = 0
        for c in cand:
            s = scan(c['chainId'], c['hook'])
            if s: f.write(s + '\n\n'); n += 1
        print(n)
