"""Coverage of the target source regions by the interpreter-trace build (hxcov),
using the cycle 12 source map of this checkout's build."""
import json, sys, os
sys.path.insert(0, os.path.abspath('../../012/theme-bytecode-coverage.work'))
import srcmap
REG = {
    'clear': ('src/PoolManager.sol', 310, 319),
    'transferFrom': ('src/ERC6909.sol', 35, 48),
    'approve': ('src/ERC6909.sol', 50, 56),
    'setOperator': ('src/ERC6909.sol', 58, 64),
    'burnFrom': ('src/ERC6909Claims.sol', 13, 22),
    'burn': ('src/PoolManager.sol', 330, 340),
    'donate(Pool)': ('src/libraries/Pool.sol', 466, 480),
    'donate(PM)': ('src/PoolManager.sol', 290, 308),
    'amount0RoundingUp': ('src/libraries/SqrtPriceMath.sol', 31, 75),
    'amount0Fallback': ('src/libraries/SqrtPriceMath.sol', 52, 52),
    'amount1RoundingDown': ('src/libraries/SqrtPriceMath.sol', 76, 125),
    'simpleMulDiv': ('src/libraries/UnsafeMath.sol', 1, 40),
}
def main():
    hits = set()
    for f in sys.argv[1:]:
        hits |= {int(x) for x in open(f).read().split()}
    out = {}
    for name, (fn, a, b) in REG.items():
        pcs = [p for p in srcmap.starts if p in srcmap.PC2I and srcmap.PC2I[p] < srcmap.NCODE and (lambda L: L['file'] == fn and L['line'] and a <= L['line'] <= b)(srcmap.loc(p))]
        h = [p for p in pcs if p in hits]
        out[name] = {'instructions': len(pcs), 'hit': len(h), 'missing': [p for p in pcs if p not in hits][:40]}
        print('%-20s %4d/%4d' % (name, len(h), len(pcs)), 'missing', out[name]['missing'][:12])
    print('total hit', len(hits), 'of', len(srcmap.starts))
    return out
if __name__ == '__main__':
    json.dump(main(), open('cov/regions.json', 'w'), indent=1)
